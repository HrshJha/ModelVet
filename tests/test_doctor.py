import json

from test_cli import invoke
from test_reports import make_report

from modelvet.core import diagnostics
from modelvet.reports.json_report import serialize_report
from modelvet.scanners.base import ToolInfo, ToolUnavailable
from modelvet.scanners.modelscan import ModelScanAdapter


def test_doctor_missing_scanner_is_explicit(monkeypatch) -> None:
    monkeypatch.setattr(ModelScanAdapter, "probe", lambda self: ToolUnavailable("Not installed."))
    result = diagnostics.diagnose()
    assert result["scanner_available"] is False
    assert result["serialized_scan_ready"] is False
    assert result["scanner_version"] is None
    assert result["scanner_reason"] == "Not installed."


def test_doctor_version_and_memory_limitations(monkeypatch) -> None:
    monkeypatch.setattr(
        ModelScanAdapter,
        "probe",
        lambda self: ToolInfo("modelscan", "0.8.8", "installed", "a" * 64),
    )
    result = diagnostics.diagnose()
    assert result["scanner_version"] == "0.8.8"
    if diagnostics.PROCESS_LIMITATIONS:
        assert result["serialized_scan_ready"] is False


def test_doctor_cli_is_script_safe_and_noninteractive() -> None:
    result = invoke("doctor", "--json")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "scanner_available" in data and data["temporary_private"] is True
    assert "not a sandbox" in data["limitations"][0]
    assert result.stderr == ""
    assert "\x1b" not in result.stdout


def test_inspect_roundtrip_does_not_rescan(tmp_path) -> None:
    report = make_report()
    path = tmp_path / "report.json"
    path.write_bytes(serialize_report(report))
    result = invoke("inspect", str(path), "--format", "json")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["decision"]["state"] == "APPROVE"
    assert data["semantic_digest"] == report.semantic_digest
    assert "signature" in data["notice"]
    result = invoke("inspect", str(path), "--show-evidence")
    assert result.returncode == 0 and "Stored decision: APPROVE" in result.stdout


def test_inspect_missing_malformed_and_unknown_schema_fail_40(tmp_path) -> None:
    path = tmp_path / "report.json"
    for raw in (None, b"not-json", b'{"schema_version":"9.0.0"}'):
        if raw:
            path.write_bytes(raw)
        result = invoke("inspect", str(path), "--format", "json")
        assert result.returncode == 40
        assert result.stdout == "" and "Traceback" not in result.stderr
