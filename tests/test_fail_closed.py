import json
import os
import sys

import pytest
from fixture_factory import artifact
from test_cli import invoke
from test_modelscan_adapter import executable

from modelvet.application import scan
from modelvet.cli import main
from modelvet.reports import writer
from modelvet.reports.json_report import read_report
from modelvet.reports.writer import ReportWriteError


def install_scanner(tmp_path, monkeypatch, body, version="0.8.8"):
    binary = executable(tmp_path, body, version)
    directory = tmp_path / "bin"
    directory.mkdir()
    binary.rename(directory / "modelscan")
    monkeypatch.setenv("PATH", str(directory) + os.pathsep + "/usr/bin:/bin")


def valid_body(mode="scanned") -> str:
    return (
        """
root = sys.argv[sys.argv.index('-p')+1]
summary = {"input_path":root,"absolute_path":root,
"modelscan_version":"0.8.8","timestamp":"untrusted",
"total_issues":0,"total_issues_by_severity":{"LOW":0,"MEDIUM":0,"HIGH":0,"CRITICAL":0},
"scanned":{"total_scanned":1,"scanned_files":["weights.pkl"]},
"skipped":{"total_skipped":0,"skipped_files":[]}}
"""
        + (
            """
summary["skipped"]={"total_skipped":1,"skipped_files":[{"source":"weights.pkl","category":"SCAN_NOT_SUPPORTED","description":"Skipped"}]}
"""
            if mode in {"skipped", "conflicting"}
            else ""
        )
        + (
            """
summary["scanned"]={"total_scanned":0,"scanned_files":[]}
"""
            if mode in {"skipped", "missing"}
            else ""
        )
        + """
Path(sys.argv[sys.argv.index('--output-file')+1]).write_text(json.dumps({"summary":summary,"issues":[],"errors":[]}))
"""
    )


@pytest.mark.parametrize(
    "fault",
    [
        "exit2",
        "exit3",
        "exit4",
        "unknown_exit",
        "timeout",
        "malformed",
        "empty",
        "overflow",
        "skipped",
        "conflicting",
        "missing",
    ],
)
def test_scanner_faults_produce_insufficient_report(tmp_path, monkeypatch, fault) -> None:
    root = artifact(tmp_path / "artifact", "serialized")
    body = valid_body()
    if fault.startswith("exit"):
        body += f"\nsys.exit({fault[-1]})"
    elif fault == "unknown_exit":
        body += "\nsys.exit(7)"
    elif fault == "timeout":
        body = "time.sleep(5)"
    elif fault == "malformed":
        body = "Path(sys.argv[sys.argv.index('--output-file')+1]).write_text('{bad')"
    elif fault == "empty":
        body = "pass"
    elif fault == "overflow":
        body = "print('x'*(1024*1024+1))"
    elif fault in {"skipped", "conflicting", "missing"}:
        body = valid_body(fault)
    install_scanner(tmp_path, monkeypatch, body)
    out = tmp_path / "reports"
    result = invoke("scan", str(root), "--out", str(out), "--timeout-sec", "1", "--json-summary")
    assert result.returncode == 30, result.stderr
    report = read_report(out / json.loads(result.stdout)["report"])
    assert report.decision.state == "INSUFFICIENT"
    assert any(
        c.check_id == "modelscan" and c.status != "COMPLETE"
        for c in report.checks
        if c.file_id == next(f.file_id for f in report.files if f.relpath == "weights.pkl")
    )
    assert report.raw_evidence


@pytest.mark.parametrize("version", [None, "0.0.0"])
def test_missing_or_wrong_version_scanner_is_not_approval(tmp_path, monkeypatch, version) -> None:
    root = artifact(tmp_path / "artifact", "serialized")
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    if version:
        install_scanner(tmp_path, monkeypatch, "pass", version)
    out = tmp_path / "out"
    result = invoke("scan", str(root), "--out", str(out), "--json-summary")
    assert result.returncode == 30, result.stderr
    report = read_report(out / json.loads(result.stdout)["report"])
    assert any(c.status == "NOT_RUN" and c.check_id == "modelscan" for c in report.checks)


@pytest.mark.parametrize("fault", ["interrupt", "writer", "drift", "unreadable"])
def test_orchestration_failures_have_correct_exit_classes(
    tmp_path, monkeypatch, capsys, fault
) -> None:
    root = artifact(tmp_path / "artifact")
    out = tmp_path / "out"
    expected = 30
    if fault == "interrupt":

        def interrupt(*args, **kwargs):
            raise KeyboardInterrupt

        monkeypatch.setattr(scan, "final_identity_checks", interrupt)
        expected = 130
    elif fault == "writer":

        def failure(*args, **kwargs):
            raise ReportWriteError("Simulated output failure")

        monkeypatch.setattr(writer, "_atomic", failure)
        expected = 50
    elif fault == "drift":
        original = scan.final_identity_checks

        def mutate(snapshot, manifest, checks):
            (root / "config.json").write_text("changed")
            return original(snapshot, manifest, checks)

        monkeypatch.setattr(scan, "final_identity_checks", mutate)
    elif fault == "unreadable":
        if os.geteuid() == 0:
            pytest.skip("Root bypasses mode bits")
        (root / "config.json").chmod(0)
        expected = 40
    monkeypatch.setattr(
        sys, "argv", ["modelvet", "scan", str(root), "--out", str(out), "--json-summary"]
    )
    with pytest.raises(SystemExit) as caught:
        main.app()
    assert caught.value.code == expected
    captured = capsys.readouterr()
    assert "APPROVE" not in captured.out + captured.err
    if expected != 30:
        assert not list(out.rglob("report.json"))
    else:
        assert json.loads(captured.out)["decision"] == "INSUFFICIENT"


def test_unsafe_paths_and_budgets_fail_without_report(tmp_path) -> None:
    root = artifact(tmp_path / "artifact")
    for arguments in (("--out", str(root / "reports")), ("--max-files", "1")):
        result = invoke("scan", str(root), *arguments, "--json-summary")
        assert result.returncode == 40 and result.stdout == ""
