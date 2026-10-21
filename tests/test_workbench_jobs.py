"""FR-025 real worker decisions, parity, interruption and persistence."""

import os
import subprocess
import sys
import time

import pytest
from fixture_factory import artifact, controlled_policy

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from workbench_helpers import ORIGIN, TOKEN
from workbench_helpers import ui as ui

from modelvet.application.scan import ScanRequest, ScanService
from modelvet.workbench.app import create_app


def wait_job(client, key, timeout=20):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        response = client.get(f"/api/v1/scans/{key}")
        assert response.status_code == 200, response.text
        record = response.json()
        if record["status"] not in {"running", "cancelling"}:
            return record
        time.sleep(0.03)
    pytest.fail("Worker did not reach a terminal state")


@pytest.mark.parametrize(
    "variant,decision",
    [
        ("clean", "APPROVE"),
        ("source", "BLOCK"),
        ("malformed", "INSUFFICIENT"),
        ("unknown", "INSUFFICIENT"),
        ("missing_claim", "INSUFFICIENT"),
        ("serialized", "INSUFFICIENT"),
    ],
)
def test_worker_decisions_and_cleanup(ui, variant, decision) -> None:
    client, root, workspace, _ = ui
    artifact(root / "candidate", variant)
    response = client.post("/api/v1/scans", json={"model_path": "candidate", "scanner": "none"})
    assert response.status_code == 202, response.text
    job = wait_job(client, response.json()["id"])
    assert job["status"] == "completed", job
    stored = client.get(f"/api/v1/reports/{job['report_id']}").json()
    assert stored["decision"] == decision
    assert not list((workspace / "staging").iterdir())
    assert not list((workspace / "tasks").iterdir())


def test_worker_cli_parity_and_controls(ui, tmp_path) -> None:
    client, root, _, _ = ui
    source = artifact(root / "candidate")
    selected = controlled_policy(tmp_path / "controls.toml")
    policy_id = client.post("/api/v1/policies", json={"toml": selected.read_text()}).json()["id"]
    job = wait_job(
        client,
        client.post(
            "/api/v1/scans", json={"model_path": "candidate", "policy_id": policy_id}
        ).json()["id"],
    )
    stored = client.get(f"/api/v1/reports/{job['report_id']}").json()
    assert stored["decision"] == "CONTROLS"
    stages = []
    direct = ScanService().run(
        ScanRequest(source, tmp_path / "cli-report", selected), on_progress=stages.append
    )
    assert stored["semantic_digest"] == direct.report.semantic_digest
    assert stages == [
        "validation",
        "snapshot",
        "inventory",
        "structural",
        "metadata",
        "scanner",
        "policy",
        "integrity",
        "report",
    ]


def test_observer_failure_cannot_change_decision(tmp_path) -> None:
    source = artifact(tmp_path / "candidate")

    def broken(stage):
        raise OSError("observational transport unavailable")

    ordinary = ScanService().run(ScanRequest(source, tmp_path / "ordinary"))
    observed = ScanService().run(ScanRequest(source, tmp_path / "observed"), on_progress=broken)
    assert ordinary.report.semantic_digest == observed.report.semantic_digest


def test_cancel_kills_scanner_and_cleans_snapshot(ui, tmp_path, monkeypatch) -> None:
    client, root, workspace, _ = ui
    artifact(root / "candidate", "serialized")
    directory = tmp_path / "trusted-scanner"
    directory.mkdir()
    marker = tmp_path / "scanner.pid"
    binary = directory / "modelscan"
    binary.write_text(
        f"#!{sys.executable}\nimport os,sys,time\nfrom pathlib import Path\n"
        "if '--version' in sys.argv:\n print('modelscan, version 0.8.8');sys.exit(0)\n"
        f"Path({str(marker)!r}).write_text(str(os.getpid()))\ntime.sleep(30)\n"
    )
    binary.chmod(0o700)
    monkeypatch.setenv("PATH", str(directory) + ":/usr/bin:/bin")
    key = client.post("/api/v1/scans", json={"model_path": "candidate"}).json()["id"]
    deadline = time.monotonic() + 10
    while not marker.exists() and time.monotonic() < deadline:
        time.sleep(0.03)
    assert marker.exists()
    assert client.post("/api/v1/scans", json={"model_path": "candidate"}).status_code == 409
    assert client.post(f"/api/v1/scans/{key}/cancel", json={}).status_code == 200
    job = wait_job(client, key)
    assert job["status"] == "cancelled" and job["report_id"] is None
    assert client.get("/api/v1/reports").json()["total"] == 0
    assert not list((workspace / "staging").iterdir())
    pid = int(marker.read_text())
    result = subprocess.run(
        ["/bin/ps", "-o", "state=", "-p", str(pid)], capture_output=True, text=True, timeout=5
    )
    assert not result.stdout.strip() or result.stdout.strip().startswith("Z")


def test_index_write_failure_never_completes(ui, monkeypatch) -> None:
    client, root, _, app = ui
    artifact(root / "candidate")

    def fail(*args, **kwargs):
        raise OSError("disk unavailable")

    monkeypatch.setattr(app.state.store, "add_report", fail)
    key = client.post("/api/v1/scans", json={"model_path": "candidate"}).json()["id"]
    record = wait_job(client, key)
    assert record["status"] == "failed" and record["report_id"] is None
    assert client.get("/api/v1/reports").json()["total"] == 0


def test_history_persists_and_unfinished_jobs_become_interrupted(tmp_path) -> None:
    root = tmp_path / "models"
    root.mkdir()
    artifact(root / "candidate")
    workspace = tmp_path / "workspace"
    app = create_app(root, workspace, ORIGIN, launch_token=TOKEN)
    with TestClient(app, base_url=ORIGIN) as client:
        response = client.post("/api/v1/session", json={"token": TOKEN}, headers={"origin": ORIGIN})
        client.headers.update({"origin": ORIGIN, "x-csrf-token": response.json()["csrf_token"]})
        key = client.post("/api/v1/scans", json={"model_path": "candidate"}).json()["id"]
        assert wait_job(client, key)["status"] == "completed"
        interrupted = app.state.store.job(key).model_copy(
            update={"id": "a" * 32, "status": "running", "report_id": None}
        )
        app.state.store.save_job(interrupted)
    reopened = create_app(root, workspace, ORIGIN, launch_token=TOKEN)
    with TestClient(reopened, base_url=ORIGIN) as client:
        client.post("/api/v1/session", json={"token": TOKEN}, headers={"origin": ORIGIN})
        assert client.get("/api/v1/reports").json()["total"] == 1
        assert client.get(f"/api/v1/reports/{key}").json()["decision"] == "APPROVE"
        assert client.get("/api/v1/scans/" + "a" * 32).json()["status"] == "interrupted"
    assert os.stat(workspace / "history.sqlite3").st_mode & 0o777 == 0o600
