import json
from pathlib import Path

import pytest
from fixture_factory import artifact, controlled_policy
from pydantic import ValidationError
from test_cli import invoke
from test_report_audit import saved

from modelvet.application.scan import ScanRequest, ScanService
from modelvet.core.errors import InvalidInput
from modelvet.reports import compare as comparison
from modelvet.reports.compare import ReportComparison, compare_reports


def scan(root, out, policy=None):
    return ScanService().run(ScanRequest(root, out, policy, scanner="none")).json_path


def test_identical_semantics_separate_from_run_bytes(tmp_path):
    root = artifact(tmp_path / "model")
    before = scan(root, tmp_path / "before")
    after = scan(root, tmp_path / "after")
    result = compare_reports(before, after)
    assert result.same_semantics and result.same_artifact and result.same_policy
    assert not result.same_report_bytes
    assert result.changed_file_count == result.changed_check_count == 0
    assert not result.admission_recomputed
    assert compare_reports(before, before).same_report_bytes


@pytest.mark.parametrize("change", ["bytes", "add", "remove"])
def test_changed_files_and_evidence_are_counted_without_paths_by_default(tmp_path, change):
    root = artifact(tmp_path / "model")
    before = scan(root, tmp_path / "before")
    if change == "bytes":
        target = root / "weights.safetensors"
        target.write_bytes(target.read_bytes()[:-4] + b"\1" * 4)
    elif change == "add":
        (root / "private-name.bin").write_bytes(b"\0unknown")
    else:
        (root / "README.md").unlink()
    after = scan(root, tmp_path / "after")
    result = compare_reports(before, after)
    assert not result.same_semantics and not result.same_artifact
    assert result.changed_file_count == 1 and result.changed_check_count > 0
    assert all(row.relpath is None for row in (*result.files, *result.checks))
    assert "private-name" not in result.model_dump_json()
    visible = compare_reports(before, after, show_paths=True)
    assert visible.files[0].relpath
    assert (
        visible.files[0].kind == {"bytes": "CHANGED", "add": "ADDED", "remove": "REMOVED"}[change]
    )
    hidden = compare_reports(before, after, max_changes=0)
    assert hidden.files == hidden.checks == ()
    assert hidden.omitted_file_changes == 1 and hidden.omitted_check_changes > 0


def test_policy_and_stored_decision_change_do_not_recalculate_admission(tmp_path):
    root = artifact(tmp_path / "model")
    before = scan(root, tmp_path / "before")
    selected = controlled_policy(tmp_path / "policy.toml")
    after = scan(root, tmp_path / "after", selected)
    result = compare_reports(before, after)
    assert result.same_artifact and not result.same_policy and not result.same_semantics
    assert result.stored_decision_before == "APPROVE" and result.stored_decision_after == "CONTROLS"
    assert result.changed_file_count == 0
    assert "policy" in result.changed_sections and "decision" in result.changed_sections
    assert "Fixture deployment owner" not in result.model_dump_json()


def test_raw_payload_declarations_are_observational(tmp_path):
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    before, _ = saved(left, (b"before",))
    after, _ = saved(right, (b"after",))
    result = compare_reports(before, after)
    assert result.same_semantics and not result.same_declared_raw
    # Comparing stored assertions never opens raw bytes or treats them as authenticated.
    for path in (before, after):
        for raw in (path.parent / "raw").iterdir():
            raw.unlink()
    assert compare_reports(before, after).same_semantics


@pytest.mark.parametrize("limit", [-1, 201, True])
def test_bad_comparison_limits(tmp_path, limit):
    path, _ = saved(tmp_path)
    with pytest.raises(InvalidInput):
        compare_reports(path, path, max_changes=limit)


def test_source_identity_recheck(tmp_path, monkeypatch):
    path, _ = saved(tmp_path)
    original = comparison.read_report_bytes
    calls = 0

    def different(selected):
        nonlocal calls
        calls += 1
        return original(selected) + (b" " if calls > 2 else b"")

    monkeypatch.setattr(comparison, "read_report_bytes", different)
    with pytest.raises(InvalidInput, match="changed"):
        compare_reports(path, path)


def test_comparison_schema_and_accounting(tmp_path):
    root = Path(__file__).parents[1]
    assert ReportComparison.model_json_schema() == json.loads(
        (root / "schemas/report-comparison-v1.json").read_text()
    )
    path, _ = saved(tmp_path)
    result = compare_reports(path, path)
    assert ReportComparison.model_validate_json(result.model_dump_json()) == result
    data = result.model_dump(mode="json")
    data["same_semantics"] = False
    with pytest.raises(ValidationError):
        ReportComparison.model_validate_json(json.dumps(data))


def test_compare_cli_changes_and_error_codes(tmp_path):
    root = artifact(tmp_path / "model")
    before = scan(root, tmp_path / "before")
    (root / "modeling.py").write_text("# Inert comment only.\n")
    after = scan(root, tmp_path / "after")
    result = invoke("compare", str(before), str(after))
    assert result.returncode == 0 and not json.loads(result.stdout)["same_semantics"]
    assert str(tmp_path) not in result.stdout + result.stderr
    assert "modeling.py" not in result.stdout
    result = invoke("compare", str(before), str(after), "--fail-on-change")
    assert result.returncode == 30
    result = invoke("compare", str(before), str(before), "--fail-on-change")
    assert result.returncode == 0
    result = invoke("compare", str(before), str(after), "--show-paths")
    assert "modeling.py" in result.stdout
    after.write_text("invalid")
    result = invoke("compare", str(before), str(after))
    assert result.returncode == 40 and result.stdout == ""


def test_unrecognized_check_names_and_free_text_are_suppressed(tmp_path):
    from test_policy import fixture
    from test_reports import make_report

    from modelvet.inventory.classify import FileFormat
    from modelvet.reports.writer import ReportWriter

    left, _ = saved(tmp_path)
    _, _, checks = fixture(FileFormat.SAFETENSORS, FileFormat.JSON)
    checks.append(
        checks[0].model_copy(
            update={"check_id": "unlisted-TOPSECRET", "details": {"note": "TOPSECRET"}}
        )
    )
    report = make_report(checks=checks)
    right, _ = ReportWriter().write(report, tmp_path / "other", artifact_dir=tmp_path / "input")
    result = compare_reports(left, right)
    assert "TOPSECRET" not in result.model_dump_json()
    assert any(c.check_id.startswith("unrecognized:") for c in result.checks)
