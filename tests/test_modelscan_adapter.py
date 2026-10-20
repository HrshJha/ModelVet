import json
import sys
from pathlib import Path

import pytest

from modelvet.core.limits import ScanLimits
from modelvet.core.snapshot import Snapshotter
from modelvet.inventory.gate import InputGate
from modelvet.scanners.modelscan import ModelScanAdapter


def executable(tmp_path: Path, body: str, version: str = "0.8.8") -> Path:
    path = tmp_path / "fake scanner; literal"
    path.write_text(
        f"#!{sys.executable}\nimport json, os, sys, time\nfrom pathlib import Path\n"
        f"if '--version' in sys.argv:\n    print('modelscan, version {version}')\n    sys.exit(0)\n"
        + body
        + "\n"
    )
    path.chmod(0o700)
    return path


def run_adapter(tmp_path: Path, binary: Path, timeout: int = 5, output_limit: int = 1024 * 1024):
    source = tmp_path / "input"
    source.mkdir(exist_ok=True)
    (source / "weights.pkl").write_bytes(b"inert scanner fixture")
    workdir = tmp_path / "work"
    workdir.mkdir(mode=0o700, exist_ok=True)
    validated = InputGate().validate(source, tmp_path / "out", ScanLimits())
    with Snapshotter(tmp_path).create(validated) as snapshot:
        result = ModelScanAdapter(binary, output_limit).run(snapshot, timeout, workdir)
    assert list(workdir.iterdir()) == []
    return result


def response(body: bytes = b"{}", exit_code: int = 0) -> str:
    return (
        "target=Path(sys.argv[sys.argv.index('--output-file')+1])\n"
        f"target.write_bytes({body!r})\nprint('bounded stdout')\n"
        f"print('bounded stderr',file=sys.stderr)\nsys.exit({exit_code})"
    )


@pytest.mark.parametrize(
    "exit_code,status",
    [
        (0, "COMPLETE"),
        (1, "COMPLETE"),
        (2, "FAILED"),
        (3, "UNSUPPORTED"),
        (4, "FAILED"),
        (7, "FAILED"),
    ],
)
def test_exit_contract(tmp_path: Path, exit_code: int, status: str) -> None:
    binary = executable(tmp_path, response(exit_code=exit_code))
    result = run_adapter(tmp_path, binary)
    assert result.status == status
    assert result.exit_code == exit_code
    assert result.report == b"{}"
    assert result.stdout == b"bounded stdout\n" and result.stderr == b"bounded stderr\n"
    assert result.argv[0] == str(binary)
    assert result.artifact_digest.startswith("sha256:")


def test_malformed_json_preserves_raw_and_status(tmp_path: Path) -> None:
    result = run_adapter(tmp_path, executable(tmp_path, response(b"{")))
    assert result.status == "FAILED"
    assert result.report == b"{" and result.exit_code == 0
    assert result.stderr == b"bounded stderr\n"


def test_missing_report_is_not_empty_success(tmp_path: Path) -> None:
    result = run_adapter(tmp_path, executable(tmp_path, "print('no report')"))
    assert result.status == "FAILED" and result.report == b""


def test_version_mismatch_does_not_scan(tmp_path: Path) -> None:
    marker = tmp_path / "must-not-exist"
    binary = executable(tmp_path, f"Path({str(marker)!r}).write_text('executed')", version="0.0.1")
    result = run_adapter(tmp_path, binary)
    assert result.status == "NOT_RUN" and not marker.exists()


def test_missing_tool_explicit(tmp_path: Path) -> None:
    assert run_adapter(tmp_path, tmp_path / "missing").status == "NOT_RUN"


def test_timeout_and_cleanup(tmp_path: Path) -> None:
    result = run_adapter(tmp_path, executable(tmp_path, "time.sleep(5)"), timeout=1)
    assert result.status == "FAILED" and result.reason == "TIMEOUT"


def test_output_limit(tmp_path: Path) -> None:
    result = run_adapter(tmp_path, executable(tmp_path, "print('x'*10000)"), output_limit=128)
    assert result.status == "FAILED" and result.reason == "OUTPUT_LIMIT"
    assert len(result.stdout) <= 128 and len(result.stderr) <= 128


def test_environment_and_resource_limits(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TOKEN_SECRET", "must-not-leak")
    body = """import resource
target=Path(sys.argv[sys.argv.index('--output-file')+1])
target.write_text(json.dumps({'env':dict(os.environ),
    'cpu':resource.getrlimit(resource.RLIMIT_CPU),
    'files':resource.getrlimit(resource.RLIMIT_NOFILE),
    'output':resource.getrlimit(resource.RLIMIT_FSIZE)}))
"""
    result = run_adapter(tmp_path, executable(tmp_path, body))
    assert result.status == "COMPLETE"
    data = json.loads(result.report)
    assert "TOKEN_SECRET" not in data["env"] and "PYTHONPATH" not in data["env"]
    assert data["env"]["PYTHONNOUSERSITE"] == "1"
    assert data["files"] == [64, 64] and data["output"] == [4194304, 4194304]
    assert data["cpu"] == [6, 6]
    if sys.platform == "darwin":
        assert any("memory is not OS-bounded" in item for item in result.limitations)


def test_symlink_report_not_read(tmp_path: Path) -> None:
    secret = tmp_path / "outside"
    secret.write_bytes(b"never read")
    body = (
        "target=Path(sys.argv[sys.argv.index('--output-file')+1])\n"
        f"target.symlink_to({str(secret)!r})"
    )
    result = run_adapter(tmp_path, executable(tmp_path, body))
    assert result.status == "FAILED" and result.report == b""
    assert secret.read_bytes() == b"never read"


def test_artifact_cannot_supply_scanner_executable(tmp_path: Path) -> None:
    source = tmp_path / "input"
    source.mkdir()
    marker = tmp_path / "must-not-exist"
    binary = executable(source, f"Path({str(marker)!r}).write_text('executed')")
    result = run_adapter(tmp_path, binary)
    assert result.status == "NOT_RUN" and not marker.exists()


def test_skipped_file_payload_preserved(tmp_path: Path) -> None:
    payload = b'{"summary":{"skipped":{"skipped_files":[{"source":"weights.pkl"}]}}}'
    result = run_adapter(tmp_path, executable(tmp_path, response(payload)))
    assert result.report == payload
    assert result.status == "COMPLETE"  # Process completion does not claim file coverage.


def test_report_file_size_limit(tmp_path: Path) -> None:
    body = (
        "target=Path(sys.argv[sys.argv.index('--output-file')+1])\n"
        "target.write_bytes(b'x'*(5*1024*1024))"
    )
    result = run_adapter(tmp_path, executable(tmp_path, body))
    assert result.status == "FAILED"
    assert len(result.report) <= 4 * 1024 * 1024
