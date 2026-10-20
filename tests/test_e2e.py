import hashlib
import json
import subprocess
import sys
from importlib.resources import files
from pathlib import Path

import pytest
from fixture_factory import artifact, controlled_policy
from test_cli import invoke

from modelvet.reports.json_report import read_report


def test_documented_examples_match_packaged_policy_and_refuse_overwrite(tmp_path) -> None:
    root = Path(__file__).parents[1]
    assert (root / "examples/default.toml").read_bytes() == files("modelvet.policies").joinpath(
        "default.toml"
    ).read_bytes()
    target = tmp_path / "synthetic"
    command = [sys.executable, str(root / "examples/create_fixture.py"), str(target)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0
    assert invoke("scan", str(target), "--out", str(tmp_path / "out"), "--quiet").returncode == 0
    before = (target / "weights.safetensors").read_bytes()
    repeated = subprocess.run(command, capture_output=True, text=True, timeout=10)
    assert repeated.returncode != 0 and (target / "weights.safetensors").read_bytes() == before


@pytest.mark.parametrize(
    "variant,exit_code,state",
    [
        ("clean", 0, "APPROVE"),
        ("source", 20, "BLOCK"),
        ("malformed", 30, "INSUFFICIENT"),
        ("unknown", 30, "INSUFFICIENT"),
        ("serialized", 30, "INSUFFICIENT"),
        ("conflict", 30, "INSUFFICIENT"),
        ("missing_claim", 30, "INSUFFICIENT"),
    ],
)
def test_real_cli_scan_outcomes_and_reports(tmp_path, variant, exit_code, state) -> None:
    root = artifact(tmp_path / "artifact", variant)
    out = tmp_path / "reports"
    result = invoke("scan", str(root), "--out", str(out), "--scanner", "none", "--json-summary")
    assert result.returncode == exit_code, result.stderr
    summary = json.loads(result.stdout)
    assert summary["decision"] == state
    assert str(tmp_path) not in result.stdout + result.stderr
    report = read_report(out / summary["report"])
    assert report.decision.state == state
    assert report.semantic_digest == summary["semantic_digest"]
    assert (out / summary["report"]).with_suffix(".md").exists()
    for file in report.files:
        assert hashlib.sha256((root / file.relpath).read_bytes()).hexdigest() == file.sha256
    assert "Static assessment only" in (out / summary["report"]).with_suffix(".md").read_text()


def test_real_cli_controls_and_frozen_semantics(tmp_path) -> None:
    root = artifact(tmp_path / "artifact")
    selected = controlled_policy(tmp_path / "controls.toml")
    out = tmp_path / "reports"
    reports = []
    for _ in range(2):
        result = invoke(
            "scan",
            str(root),
            "--out",
            str(out),
            "--policy",
            str(selected),
            "--json-summary",
            "--quiet",
        )
        assert result.returncode == 10, result.stderr
        assert result.stderr == ""
        reports.append(read_report(out / json.loads(result.stdout)["report"]))
    assert reports[0].semantic_digest == reports[1].semantic_digest
    assert reports[0].run.run_id != reports[1].run.run_id
    assert reports[0].decision.required_controls[0].owner == "Fixture deployment owner"


@pytest.mark.parametrize("format", ["json", "markdown", "both"])
def test_output_formats_and_inspect(tmp_path, format) -> None:
    root = artifact(tmp_path / "artifact")
    out = tmp_path / "reports"
    result = invoke("scan", str(root), "--out", str(out), "--format", format, "--json-summary")
    assert result.returncode == 0, result.stderr
    path = out / json.loads(result.stdout)["report"]
    assert path.exists()
    assert path.with_suffix(".md").exists() == (format != "json")
    inspected = invoke("inspect", str(path), "--format", "json")
    assert (
        inspected.returncode == 0 and json.loads(inspected.stdout)["decision"]["state"] == "APPROVE"
    )
