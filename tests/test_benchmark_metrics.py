import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from modelvet.benchmarks.metrics import Observation, development_metrics
from modelvet.benchmarks.runner import PilotResult, run
from modelvet.core.errors import InvalidInput
from modelvet.scanners.base import RawScannerExecution
from modelvet.scanners.modelscan import ModelScanAdapter

ROOT = Path(__file__).parents[1]
MANIFEST = ROOT / "benchmarks/manifest.json"
DIGEST = "sha256:" + "a" * 64


def row(tool="modelvet", fixture="example", repeat=1, **updates):
    return Observation.model_validate(
        {
            "fixture_id": fixture,
            "artifact_digest": DIGEST,
            "tool_id": tool,
            "tool_version": "test-1",
            "repeat_id": repeat,
            "eligibility": "SUPPORTED_CONTEXT",
            "outcome": "COMPLETE_NO_FINDINGS",
            "wall_s": 0.01,
            "evidence_ref": "fixture.json",
            **updates,
        }
    )


def test_unsupported_is_never_false_negative_and_empty_denominator_unknown():
    metrics = development_metrics(
        (
            row(),
            row("modelscan", eligibility="NOT_APPLICABLE", outcome="NOT_APPLICABLE"),
        )
    )
    assert metrics["joint_context_observations"] == 0
    assert metrics["tools"]["modelscan"]["not_applicable"] == 1
    assert metrics["tools"]["modelscan"]["eligible_observations"] == 0
    for key in ("false_clean_rate", "incremental_detection_rate", "confidence_interval"):
        assert metrics[key] is None
    assert metrics["reviewed_discrepancy_denominator"] == 0


def test_paired_context_and_unavailability_are_separate():
    metrics = development_metrics(
        (
            row(),
            row("modelscan"),
            row(fixture="other"),
            row("modelscan", fixture="other", outcome="UNAVAILABLE", tool_version=None),
        )
    )
    assert metrics["joint_context_observations"] == 1
    assert metrics["tools"]["modelscan"]["unavailable"] == 1
    assert metrics["tools"]["modelscan"]["complete_no_findings"] == 1


def test_repeat_agreement_does_not_count_missing_or_unsupported():
    metrics = development_metrics(
        (
            row(),
            row(repeat=2, outcome="UNRESOLVED"),
            row("modelscan", outcome="UNAVAILABLE"),
            row("modelscan", repeat=2, outcome="UNAVAILABLE"),
        )
    )
    assert metrics["repeated_groups"] == 1 and metrics["stable_repeated_groups"] == 0


@pytest.mark.parametrize("variant", ["duplicate", "identity"])
def test_duplicate_or_mismatched_evidence_rejected(variant):
    records = (
        (row(), row())
        if variant == "duplicate"
        else (row(), row("modelscan", artifact_digest="sha256:" + "b" * 64))
    )
    with pytest.raises(InvalidInput):
        development_metrics(records)


@pytest.mark.parametrize(
    "updates",
    [
        {"outcome": "NOT_APPLICABLE"},
        {"tool_version": None},
        {"evidence_ref": None},
        {"wall_s": -1.0},
        {"wall_s": float("nan")},
        {"repeat_id": 0},
    ],
)
def test_invalid_observations(updates):
    with pytest.raises(ValidationError):
        row(**updates)


def test_scanner_exit_cannot_be_an_admission_decision():
    with pytest.raises(ValidationError):
        row("modelscan", decision="APPROVE")


def test_pilot_uses_only_safe_fixtures_and_keeps_private_complete_marker(tmp_path, monkeypatch):
    calls = []

    def unavailable(self, snapshot, timeout_s, workdir):
        from modelvet.inventory.identity import InventoryService

        calls.append(snapshot.root)
        return RawScannerExecution(
            InventoryService().collect(snapshot).manifest_digest,
            None,
            "NOT_RUN",
            reason="Injected unavailable baseline.",
        )

    monkeypatch.setattr(ModelScanAdapter, "run", unavailable)
    out = tmp_path / "pilot"
    result = run(MANIFEST, out, repeats=2)
    assert len(result.observations) == 40 and result.study_status == "INCONCLUSIVE"
    assert result.metrics["tools"]["modelscan"]["unavailable"] == 6
    assert result.metrics["tools"]["modelscan"]["not_applicable"] == 14
    assert result.metrics["joint_context_observations"] == 0
    assert result.metrics["false_clean_rate"] is None
    assert (out / "result.json").stat().st_mode & 0o777 == 0o600
    assert out.stat().st_mode & 0o777 == 0o700
    stored = PilotResult.model_validate_json((out / "result.json").read_bytes())
    assert stored == result and calls
    assert not any(path.exists() for path in calls)
    for observation in result.observations:
        if observation.evidence_ref:
            assert (out / observation.evidence_ref).is_file()
    with pytest.raises(InvalidInput):
        run(MANIFEST, out)
    data = result.model_dump(mode="json")
    data["metrics"]["joint_context_observations"] = 99
    with pytest.raises(ValidationError):
        PilotResult.model_validate_json(json.dumps(data))
    data = result.model_dump(mode="json")
    data["observations"].pop()
    with pytest.raises(ValidationError):
        PilotResult.model_validate_json(json.dumps(data))


@pytest.mark.parametrize("repeats", [0, 4, True])
def test_repeat_budgets(tmp_path, repeats):
    with pytest.raises(InvalidInput):
        run(MANIFEST, tmp_path / "bad", repeats=repeats)
    assert not (tmp_path / "bad").exists()


def test_unsafe_output_parent(tmp_path):
    (tmp_path / "alias").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(InvalidInput):
        run(MANIFEST, tmp_path / "alias" / "pilot")


def test_runner_cli_argument_error_is_controlled():
    result = subprocess.run(
        [sys.executable, "-m", "modelvet.benchmarks.runner", "--invalid"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 40 and "Traceback" not in result.stderr


def test_pilot_schema_export():
    assert PilotResult.model_json_schema() == json.loads(
        (ROOT / "schemas/benchmark-run-v1.json").read_text()
    )
