"""CLI contract tests run through the installed command boundary."""

import json
import os
import subprocess
import sys

import pytest

from modelvet.cli import main


def invoke(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "modelvet", *arguments],
        capture_output=True,
        text=True,
        timeout=10,
        env={**os.environ, "NO_COLOR": "1", "CI": "1", "COLUMNS": "150"},
    )


@pytest.mark.parametrize(
    "command",
    [[], ["scan"], ["inspect"], ["advisories"], ["doctor"], ["version"], ["policy", "validate"]],
)
def test_help_and_exit_contract(command: list[str]) -> None:
    result = invoke(*command, "--help")
    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert "\x1b" not in result.stdout + result.stderr
    assert result.stderr == ""


def test_scan_help_lists_all_flags() -> None:
    result = invoke("scan", "--help")
    for flag in (
        "--policy",
        "--out",
        "--scanner",
        "--timeout-sec",
        "--max-files",
        "--max-file-mib",
        "--max-total-mib",
        "--format",
        "--quiet",
        "--json-summary",
    ):
        assert flag in result.stdout


@pytest.mark.parametrize(
    "arguments",
    [
        ["scan"],
        ["inspect"],
        ["advisories"],
        ["policy", "validate"],
        ["unknown"],
        ["scan", ".", "--scanner", "unsafe"],
        ["scan", ".", "--timeout-sec", "0"],
        ["scan", ".", "--unknown"],
    ],
)
def test_invalid_arguments_exit_40(arguments: list[str]) -> None:
    result = invoke(*arguments)
    assert result.returncode == 40
    assert result.stdout == ""
    assert "exit 40" in result.stderr
    assert "Traceback" not in result.stderr


def test_version_reports_implemented_schema_support() -> None:
    result = invoke("version", "--json")
    assert result.returncode == 0
    assert json.loads(result.stdout) == {"modelvet_version": "0.1.0", "schema_versions": ["1.0.0"]}
    assert result.stderr == ""


@pytest.mark.parametrize("error, expected", [(KeyboardInterrupt(), 130), (RuntimeError(), 50)])
def test_boundary_errors_are_controlled(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    error: BaseException,
    expected: int,
) -> None:
    def fail(**kwargs: object) -> None:
        raise error

    monkeypatch.setattr(main, "cli", fail)
    with pytest.raises(SystemExit) as caught:
        main.app()
    assert caught.value.code == expected
    output = capsys.readouterr()
    assert output.out == ""
    assert "Traceback" not in output.err
