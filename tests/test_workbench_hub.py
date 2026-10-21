"""Hub API/worker contracts: no secret in descriptors, real engine, controlled failures."""

import json
import os
import signal
import tempfile
import uuid

import pytest
from fixture_factory import artifact
from hub_fixtures import URL, FakeHTTPS
from workbench_helpers import ui as ui

from modelvet.hub import assessment
from modelvet.workbench import worker
from modelvet.workbench.models import ScanInput


def test_source_discriminant_rejects_ambiguity_and_auth_on_local():
    for payload in (
        {},
        {"model_path": "x", "hub_url": URL},
        {"model_path": "x", "use_hf_token": True},
        {"hub_url": "https://example.test/a/b"},
    ):
        with pytest.raises(ValueError):
            ScanInput.model_validate(payload)
    assert ScanInput(hub_url=URL).model_path == ""


@pytest.mark.parametrize("enabled", [False, True])
def test_auth_only_in_explicit_worker_environment(ui, monkeypatch, enabled):
    client, _, workspace, app = ui
    secret = "hf_PRIVATELOCAL12345"
    monkeypatch.setenv("HF_TOKEN", secret)
    seen = {}

    def launch(*args, **kwargs):
        seen.update(kwargs)
        seen["argv"] = args[0]
        from pathlib import Path

        assert secret not in Path(args[0][-1]).read_text()
        # A controlled setup error prevents an actual network worker.
        raise OSError("inert fixture")

    monkeypatch.setattr("modelvet.workbench.jobs.subprocess.Popen", launch)
    with pytest.raises(OSError):
        app.state.jobs.start(ScanInput(hub_url=URL, use_hf_token=enabled))
    assert seen["env"].get("HF_TOKEN") == (secret if enabled else None)
    assert secret not in str(seen["argv"])
    assert not list((workspace / "tasks").iterdir())
    assert not list((workspace / "staging").iterdir())
    assert all(secret not in row.model_dump_json() for row in app.state.store.jobs())


@pytest.mark.parametrize("cancelled", [False, True])
def test_worker_remote_route_uses_existing_engine_and_cleans(
    ui, tmp_path, monkeypatch, capsys, cancelled
):
    client, models, workspace, app = ui
    root = artifact(tmp_path / "inert")
    files = {p.name: p.read_bytes() for p in root.iterdir()}

    def transport(**kwargs):
        result = FakeHTTPS(files)
        if cancelled:

            def interrupt(*args):
                raise KeyboardInterrupt

            result.read = interrupt
        return result

    monkeypatch.setattr(assessment, "HTTPS", transport)
    key = uuid.uuid4().hex
    (workspace / "staging" / key).mkdir(mode=0o700)
    descriptor = app.state.store.descriptor(
        key,
        {
            "id": key,
            "workspace": str(workspace),
            "workspace_identity": app.state.workspace.identity,
            "models_root": str(models),
            "model_identity": app.state.workspace.model_identity,
            "parent_pid": os.getppid(),
            "request": ScanInput(hub_url=URL).model_dump(),
        },
    )
    monkeypatch.setattr("sys.argv", ["worker", str(descriptor)])
    monkeypatch.setattr(tempfile, "tempdir", tempfile.tempdir)
    previous = {s: signal.getsignal(s) for s in (signal.SIGALRM, signal.SIGTERM)}
    try:
        code = worker.main()
    finally:
        for s, handler in previous.items():
            signal.signal(s, handler)
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    if cancelled:
        assert code == 130 and events[-1]["type"] == "cancelled"
        assert not list((workspace / "reports").iterdir())
    else:
        assert code == 0, events
        report_path = workspace / events[-1]["report_path"]
        from modelvet.reports.json_report import read_report

        report = read_report(report_path)
        assert report.source.repo_id == "example/model"
        assert report.decision.state == "APPROVE"
    assert not list((workspace / "staging" / key).iterdir())


def test_hub_capabilities_do_not_reveal_credentials(ui, monkeypatch):
    client, _, _, _ = ui
    monkeypatch.setenv("HF_TOKEN", "hf_PRIVATELOCAL12345")
    response = client.get("/api/v1/capabilities")
    assert response.json()["hub_token_configured"] is True
    assert "PRIVATELOCAL" not in response.text
