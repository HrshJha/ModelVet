"""FR-027 HTTP, process and private data boundary regressions; inert fixtures only."""

import asyncio
import errno
import json
import os
import signal
import subprocess
import sys
import time

import pytest
from fixture_factory import artifact

pytest.importorskip("fastapi")
import httpx
from fastapi.testclient import TestClient
from workbench_helpers import ORIGIN, TOKEN
from workbench_helpers import ui as ui

from modelvet.core.errors import InvalidInput
from modelvet.workbench.app import create_app
from modelvet.workbench.models import JobRecord, ScanInput
from modelvet.workbench.paths import Workspace, trusted_worker_path
from modelvet.workbench.security import BrowserSession, LocalBoundary


def test_capabilities_do_not_launch_scanners_from_request_threads(ui, monkeypatch) -> None:
    client, _, _, _ = ui

    def forbidden(**kwargs):
        raise AssertionError("Request-handler scanner probe")

    monkeypatch.setattr("modelvet.workbench.app.diagnose", forbidden)
    assert client.get("/api/v1/capabilities").status_code == 200


def test_artifact_path_scanner_is_not_probed_or_inherited(tmp_path, monkeypatch) -> None:
    models = tmp_path / "models"
    models.mkdir()
    tools = models / "untrusted-tools"
    tools.mkdir()
    marker = tmp_path / "must-not-execute"
    binary = tools / "modelscan"
    binary.write_text(
        f"#!{sys.executable}\nfrom pathlib import Path\nPath({str(marker)!r}).touch()\n"
    )
    binary.chmod(0o700)
    monkeypatch.setenv("PATH", str(tools) + ":/usr/bin:/bin")
    app = create_app(models, tmp_path / "workspace", ORIGIN, launch_token=TOKEN)
    with TestClient(app, base_url=ORIGIN) as client:
        client.post("/api/v1/session", json={"token": TOKEN}, headers={"origin": ORIGIN})
        assert client.get("/api/v1/capabilities").json()["scanner_available"] is False
        assert str(tools) not in trusted_worker_path(app.state.workspace).split(os.pathsep)
    assert not marker.exists()


def test_chunked_oversize_and_invalid_download_format(ui) -> None:
    client, _, _, _ = ui
    response = client.post(
        "/api/v1/policies",
        content=(b"x" * 1024 for _ in range(65)),
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 413
    assert client.get("/api/v1/reports/" + "a" * 32 + "/download?format=html").status_code == 422
    for value in ("../outside", "/etc/passwd", "demo-../../outside"):
        assert client.get("/api/v1/reports/" + value.replace("/", "%2F")).status_code in {400, 404}


def test_root_drift_and_linked_index_fail_closed(ui, tmp_path) -> None:
    client, root, workspace, _ = ui
    root.rename(tmp_path / "original-models")
    root.mkdir()
    assert client.get("/api/v1/directories").status_code == 400
    assert client.post("/api/v1/scans", json={"model_path": "."}).status_code == 400
    database = workspace / "history.sqlite3"
    os.link(database, tmp_path / "history-hardlink")
    assert client.get("/api/v1/reports").status_code == 400


def test_workspace_linked_subdirectory_is_rejected(tmp_path) -> None:
    models = tmp_path / "models"
    models.mkdir()
    workspace = tmp_path / "workspace"
    workspace.mkdir(mode=0o700)
    outside = tmp_path / "outside"
    outside.mkdir()
    (workspace / "policies").symlink_to(outside, target_is_directory=True)
    with pytest.raises((InvalidInput, OSError)):
        Workspace(models, workspace)
    assert not list(outside.iterdir())


def test_setup_disk_full_and_supervisor_failure_cleanup(ui, monkeypatch) -> None:
    _, root, workspace, app = ui
    artifact(root / "candidate")

    def full(*args, **kwargs):
        raise OSError(errno.ENOSPC, "injected private write failure")

    with monkeypatch.context() as patch:
        patch.setattr("modelvet.workbench.store.write_private", full)
        with pytest.raises(OSError):
            app.state.jobs.start(ScanInput(model_path="candidate"))
    assert not list((workspace / "staging").iterdir())
    assert app.state.jobs.active_id is None
    assert all(job.status == "failed" for job in app.state.store.jobs())
    import threading

    original = threading.Thread.start

    def unavailable(thread):
        if thread.name == "modelvet-scan-supervisor":
            raise RuntimeError("injected thread resource failure")
        original(thread)

    with monkeypatch.context() as patch:
        patch.setattr(threading.Thread, "start", unavailable)
        with pytest.raises(RuntimeError):
            app.state.jobs.start(ScanInput(model_path="candidate"))
    assert not list((workspace / "staging").iterdir())
    assert app.state.store.reports(0, 50).total == 0
    assert app.state.jobs.active_id is None


def test_request_concurrency_is_bounded() -> None:
    async def exercise():
        release = asyncio.Event()
        session = BrowserSession(ORIGIN)
        session.exchanged = True

        async def application(scope, receive, send):
            await release.wait()
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"{}"})

        boundary = LocalBoundary(application, session)
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/v1/session",
            "headers": [
                (b"host", b"127.0.0.1:8765"),
                (b"cookie", ("modelvet_session=" + session.session_id).encode()),
            ],
        }

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            pass

        running = [asyncio.create_task(boundary(scope, receive, send)) for _ in range(4)]
        await asyncio.sleep(0)
        responses = []

        async def captured(message):
            responses.append(message)

        await boundary(scope, receive, captured)
        assert responses[0]["status"] == 429
        release.set()
        await asyncio.gather(*running)

    asyncio.run(exercise())


@pytest.mark.parametrize(
    "body",
    [
        "print('not-json')",
        "print('x'*140000)",
        'print(\'{"type":"result","report_path":"../escape"}\')',
    ],
)
def test_worker_protocol_failures_never_create_a_report(ui, body) -> None:
    _, _, _, app = ui
    manager = app.state.jobs
    record = JobRecord(
        id="b" * 32,
        label="inert protocol fixture",
        status="running",
        stage="validation",
        started_at="2026-10-21T00:00:00Z",
    )
    app.state.store.save_job(record)
    process = subprocess.Popen(
        [sys.executable, "-I", "-c", body],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    manager.process, manager.active_id, manager.started = process, record.id, time.monotonic()
    manager.collect(record, process)
    saved = app.state.store.job(record.id)
    assert saved.status == "failed" and saved.report_id is None
    assert app.state.store.reports(0, 50).total == 0


def process_stopped(pid):
    result = subprocess.run(
        ["/bin/ps", "-o", "state=", "-p", str(pid)], capture_output=True, text=True, timeout=5
    )
    return not result.stdout.strip() or result.stdout.strip().startswith("Z")


def test_server_death_interrupts_worker_and_scanner_then_restart_recovers(tmp_path) -> None:
    root = tmp_path / "models"
    root.mkdir()
    artifact(root / "candidate", "serialized")
    workspace = tmp_path / "workspace"
    bin_dir = tmp_path / "trusted-scanner"
    bin_dir.mkdir()
    marker = tmp_path / "scanner-pid"
    scanner = bin_dir / "modelscan"
    scanner.write_text(
        f"#!{sys.executable}\nimport os,sys,time\nfrom pathlib import Path\n"
        "if '--version' in sys.argv:\n print('modelscan, version 0.8.8');sys.exit(0)\n"
        f"Path({str(marker)!r}).write_text(str(os.getpid()))\ntime.sleep(30)\n"
    )
    scanner.chmod(0o700)
    script = tmp_path / "owned-fixture-server.py"
    script.write_text("""
import json,socket,sys,uvicorn
from pathlib import Path
from modelvet.workbench.app import create_app
listener=socket.socket(); listener.bind(('127.0.0.1',0)); listener.listen(32)
port=listener.getsockname()[1]
app=create_app(Path(sys.argv[1]),Path(sys.argv[2]),f'http://127.0.0.1:{port}',launch_token=sys.argv[3])
print(json.dumps({'port':port}),flush=True)
uvicorn.Server(uvicorn.Config(app,log_level='critical',access_log=False,proxy_headers=False)).run(sockets=[listener])
""")
    server = subprocess.Popen(
        [sys.executable, "-I", str(script), str(root), str(workspace), TOKEN],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "PATH": str(bin_dir) + ":/usr/bin:/bin"},
    )
    try:
        assert server.stdout is not None
        port = json.loads(server.stdout.readline())["port"]
        origin = f"http://127.0.0.1:{port}"
        with httpx.Client(base_url=origin, trust_env=False, timeout=10) as client:
            response = client.post(
                "/api/v1/session", json={"token": TOKEN}, headers={"origin": origin}
            )
            client.headers.update({"origin": origin, "x-csrf-token": response.json()["csrf_token"]})
            key = client.post("/api/v1/scans", json={"model_path": "candidate"}).json()["id"]
            deadline = time.monotonic() + 10
            while not marker.exists() and time.monotonic() < deadline:
                time.sleep(0.03)
            assert marker.exists()
            child = subprocess.run(
                ["pgrep", "-P", str(server.pid)], capture_output=True, text=True, timeout=5
            )
            worker = int(child.stdout.strip())
            scanner_pid = int(marker.read_text())
            server.kill()
            server.wait(timeout=5)
            deadline = time.monotonic() + 7
            while (
                not process_stopped(worker) or not process_stopped(scanner_pid)
            ) and time.monotonic() < deadline:
                time.sleep(0.05)
            assert process_stopped(worker) and process_stopped(scanner_pid)
        reopened = create_app(root, workspace, ORIGIN, launch_token=TOKEN)
        with TestClient(reopened, base_url=ORIGIN) as client:
            client.post("/api/v1/session", json={"token": TOKEN}, headers={"origin": ORIGIN})
            assert client.get(f"/api/v1/scans/{key}").json()["status"] == "interrupted"
            assert client.get("/api/v1/reports").json()["total"] == 0
            assert not list((workspace / "staging").iterdir())
    finally:
        if server.poll() is None:
            server.send_signal(signal.SIGTERM)
            server.wait(timeout=15)
        if server.stdout is not None:
            server.stdout.close()
        if server.stderr is not None:
            server.stderr.close()
