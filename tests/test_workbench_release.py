"""Exercise a fresh UI wheel without Node on the application PATH or remote sockets."""

import ipaddress
import os
import select
import shutil
import signal
import subprocess
import sys
import tarfile
import time
import zipfile
from pathlib import Path

import pytest
from test_release import ROOT, command

pytest.importorskip("fastapi")


@pytest.fixture(scope="module")
def ui_candidate(tmp_path_factory):
    parent = tmp_path_factory.mktemp("ui-installed").resolve()
    dist = parent / "dist"
    command(["uv", "build", "--offline", "--out-dir", str(dist)])
    wheel = next(dist.glob("*.whl"))
    archive = next(dist.glob("*.tar.gz"))
    requirements = parent / "runtime.txt"
    command(
        [
            "uv",
            "export",
            "--locked",
            "--extra",
            "ui",
            "--no-dev",
            "--no-emit-project",
            "--format",
            "requirements-txt",
            "--output-file",
            str(requirements),
        ]
    )
    command(["uv", "venv", "--python", sys.executable, str(parent / "venv")])
    python = parent / "venv/bin/python"
    command(
        [
            "uv",
            "pip",
            "sync",
            "--offline",
            "--python",
            str(python),
            "--require-hashes",
            "--only-binary",
            ":all:",
            str(requirements),
        ]
    )
    command(["uv", "pip", "install", "--offline", "--python", str(python), "--no-deps", str(wheel)])
    command(["uv", "pip", "check", "--python", str(python)])
    site = Path(
        command(
            [
                str(python),
                "-I",
                "-c",
                "import sysconfig; print(sysconfig.get_path('purelib'))",
            ]
        ).stdout.strip()
    )
    # Trusted acceptance instrumentation installed ONLY in this disposable test environment.
    # -I still loads environment site-packages, so the own-module worker inherits this guard.
    (site / "modelvet_acceptance_guard.py").write_text("""
import ipaddress
import socket
_original_connect = socket.socket.connect
_original_connect_ex = socket.socket.connect_ex
def local(address):
    if not isinstance(address, tuple) or not ipaddress.ip_address(address[0]).is_loopback:
        raise AssertionError("External network denied by acceptance instrumentation")
def connect(self, address):
    local(address)
    return _original_connect(self, address)
def connect_ex(self, address):
    local(address)
    return _original_connect_ex(self, address)
socket.socket.connect = connect
socket.socket.connect_ex = connect_ex
""")
    (site / "modelvet_acceptance_guard.pth").write_text("import modelvet_acceptance_guard\n")
    empty_path = parent / "empty-path"
    empty_path.mkdir()
    models = parent / "models"
    models.mkdir()
    command([str(python), str(ROOT / "examples/create_fixture.py"), str(models / "tiny")])
    environment = {"PATH": str(empty_path), "HOME": str(parent), "NO_COLOR": "1"}
    process = subprocess.Popen(
        [
            str(python),
            "-I",
            "-m",
            "modelvet",
            "ui",
            "--models-root",
            str(models),
            "--workspace",
            str(parent / "workspace"),
            "--no-browser",
        ],
        cwd=parent,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        shell=False,
        start_new_session=True,
    )
    try:
        lines = []
        deadline = time.monotonic() + 20
        # Read bytes: TextIO buffering can hide the second line from select().
        captured = b""
        while captured.count(b"\n") < 2 and time.monotonic() < deadline:
            if select.select([process.stdout], [], [], 0.2)[0]:
                captured += os.read(process.stdout.fileno(), 4096)
            assert process.poll() is None, "Installed workbench exited before launch"
        lines = captured.decode().splitlines()
        assert len(lines) >= 2, "Installed workbench did not launch"
        link = lines[1].split("Private one-use launch link: ", 1)[1]
        origin, token = link.split("/#launch=")
        assert ipaddress.ip_address(origin.split("://")[1].split(":")[0]).is_loopback
        import httpx

        with httpx.Client(base_url=origin, timeout=15, trust_env=False) as client:
            for _ in range(100):
                try:
                    if client.get("/").status_code == 200:
                        break
                except httpx.ConnectError:
                    pass
                time.sleep(0.05)
            login = client.post(
                "/api/v1/session", json={"token": token}, headers={"origin": origin}
            )
            assert login.status_code == 200
            client.headers.update({"origin": origin, "x-csrf-token": login.json()["csrf_token"]})
            yield parent, python, wheel, archive, client, process
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGINT)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
        process.stdout.close()
        process.stderr.close()


def test_ui_distribution_is_self_contained(ui_candidate):
    parent, python, wheel, archive, client, _ = ui_candidate
    with zipfile.ZipFile(wheel) as package:
        names = package.namelist()
        assert "modelvet/workbench/static/index.html" in names
        assert sum(name.startswith("modelvet/workbench/demo/demo-") for name in names) == 4
        notices = package.read("modelvet/workbench/static/THIRD_PARTY_NOTICES.txt").decode()
        assert "React" in notices or "react" in notices
        assert "Permission is hereby granted" in notices
        assert any(name.endswith(".js") and "/static/assets/" in name for name in names)
    with tarfile.open(archive) as package:
        names = package.getnames()
        for suffix in (
            "frontend/package-lock.json",
            "frontend/scripts/notices.mjs",
            "tools/workbench_schema.py",
            "frontend/src/App.tsx",
        ):
            assert any(name.endswith("/" + suffix) for name in names)
        assert not any(
            part in name
            for name in names
            for part in (
                "/node_modules/",
                "/test-results/",
                "/playwright-report/",
                "/docs/verification/",
            )
        )
    result = command(
        [str(python), "-I", "-c", "import modelvet; print(modelvet.__file__)"], cwd=parent
    )
    assert str(parent / "venv") in result.stdout and str(ROOT / "src") not in result.stdout
    assert client.get("/api/v1/capabilities").json()["scanner_available"] is False
    assert len(client.get("/api/v1/demos").json()) == 4
    # Guard is loaded in isolated server/worker environments, not just the pytest parent.
    blocked = subprocess.run(
        [
            str(python),
            "-I",
            "-c",
            "import socket; socket.socket().connect(('203.0.113.1',443))",
        ],
        cwd=parent,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert blocked.returncode != 0 and "External network denied" in blocked.stderr


def test_installed_workflow_without_node_or_external_network(ui_candidate):
    _, _, _, _, client, _ = ui_candidate
    started = client.post("/api/v1/scans", json={"model_path": "tiny", "scanner": "none"})
    assert started.status_code == 202, started.text
    key = started.json()["id"]
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        job = client.get(f"/api/v1/scans/{key}").json()
        if job["status"] not in {"running", "cancelling"}:
            break
        time.sleep(0.05)
    assert job["status"] == "completed", job
    report_id = job["report_id"]
    summary = client.get(f"/api/v1/reports/{report_id}").json()
    assert summary["decision"] == "APPROVE"
    raw = client.get(f"/api/v1/reports/{report_id}/download").content
    imported = client.post(
        "/api/v1/reports/import", content=raw, headers={"content-type": "application/json"}
    )
    assert imported.status_code == 201
    comparison = client.post(
        "/api/v1/comparisons",
        json={
            "before_id": report_id,
            "after_id": imported.json()["id"],
        },
    )
    assert comparison.status_code == 200 and comparison.json()["same_semantics"]
    assert (
        client.post(f"/api/v1/reports/{report_id}/verify", json={}).json()["status"] == "VERIFIED"
    )
    assert client.get("/api/v1/reports").json()["total"] == 2


def test_installed_browser_smoke(ui_candidate):
    """Node is a test driver only; it is absent from the application's inherited PATH."""
    *_, client, process = ui_candidate
    node = shutil.which("node")
    if node is None or not (ROOT / "frontend/node_modules/@playwright/test").exists():
        if os.environ.get("CI"):
            pytest.fail("CI must install the pinned browser test driver")
        pytest.skip("Browser development dependencies unavailable")
    environment = {
        **os.environ,
        "MODELVET_ACCEPTANCE_ORIGIN": str(client.base_url).rstrip("/"),
        "MODELVET_ACCEPTANCE_COOKIE": client.cookies.get("modelvet_session"),
    }
    result = subprocess.run(
        [node, "scripts/installed-smoke.mjs"],
        cwd=ROOT / "frontend",
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert process.poll() is None
