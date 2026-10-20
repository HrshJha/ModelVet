import hashlib
import json
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from modelvet.core.errors import InvalidInput
from modelvet.coverage.reconciler import CoverageReconciler, expectations_for
from modelvet.evidence.models import (
    CheckRecord,
    CheckResult,
    CheckStatus,
    CoverageRecord,
    ExpectedCheck,
)
from modelvet.inventory.classify import FileClassification, FileFormat
from modelvet.inventory.discover import FileObservation
from modelvet.inventory.identity import manifest_from_entries


def fixture():
    manifest = manifest_from_entries(
        tuple(
            FileObservation(name, 1, hashlib.sha256(b"x").hexdigest())
            for name in ("a.pkl", "b.pkl")
        )
    )
    expected = [
        ExpectedCheck(file_id=file.file_id, check_id="modelscan") for file in manifest.files
    ]
    return manifest, expected


def record(manifest, file, status: CheckStatus, executor: str = "modelscan") -> CheckRecord:
    return CheckRecord(
        file_id=file.file_id,
        check_id="modelscan",
        executor_id=executor,
        status=status,
        result=CheckResult.NO_FINDINGS if status == CheckStatus.COMPLETE else CheckResult.UNKNOWN,
        artifact_digest=manifest.manifest_digest,
    )


@pytest.mark.parametrize("status", list(CheckStatus))
def test_terminal_partition_and_missing_file(status: CheckStatus) -> None:
    manifest, expected = fixture()
    result = CoverageReconciler().reconcile(
        manifest, expected, [record(manifest, manifest.files[0], status)]
    )
    first, missing = result
    assert (first.mandatory_unresolved == ()) == (status == CheckStatus.COMPLETE)
    assert missing.inconclusive_check_ids == ("modelscan",)
    assert missing.mandatory_unresolved == ("modelscan",)


@given(st.lists(st.sampled_from(list(CheckStatus)), max_size=8))
def test_reordering_never_selects_a_favorable_duplicate(statuses: list[CheckStatus]) -> None:
    manifest, expected = fixture()
    records = [
        record(manifest, manifest.files[0], status, f"producer-{i}")
        for i, status in enumerate(statuses)
    ]
    first = CoverageReconciler().reconcile(manifest, expected, records)
    assert first == CoverageReconciler().reconcile(manifest, expected, list(reversed(records)))
    if len(records) != 1:
        assert first[0].mandatory_unresolved == ("modelscan",)


def test_wrong_artifact_and_unknown_file_rejected() -> None:
    manifest, expected = fixture()
    wrong = record(manifest, manifest.files[0], CheckStatus.COMPLETE).model_copy(
        update={"artifact_digest": "sha256:" + "f" * 64}
    )
    assert CoverageReconciler().reconcile(manifest, expected, [wrong])[0].mandatory_unresolved
    unknown = wrong.model_copy(update={"file_id": "f" * 64})
    with pytest.raises(InvalidInput):
        CoverageReconciler().reconcile(manifest, expected, [unknown])


def test_duplicate_expectations_not_silently_deduplicated() -> None:
    manifest, expected = fixture()
    with pytest.raises(InvalidInput):
        CoverageReconciler().reconcile(manifest, expected + [expected[0]], [])


def test_optional_missing_stays_visible() -> None:
    manifest, expected = fixture()
    optional = [item.model_copy(update={"mandatory": False}) for item in expected]
    results = CoverageReconciler().reconcile(manifest, optional, [])
    assert all(not row.mandatory_unresolved and row.inconclusive_check_ids for row in results)


def test_expected_registry_ignores_producer_check_list() -> None:
    manifest, _ = fixture()
    classes = {
        file.file_id: FileClassification(FileFormat.PICKLE_LIKE, ()) for file in manifest.files
    }
    expected = expectations_for(manifest, classes)
    assert {"modelscan", "scanner:resources", "identity", "classification"} == {
        item.check_id for item in expected
    }
    assert all(item.mandatory for item in expected)


def test_invalid_wire_partition_rejected() -> None:
    manifest, expected = fixture()
    row = CoverageReconciler().reconcile(manifest, expected, [])[0].model_dump(mode="json")
    with pytest.raises(ValidationError):
        CoverageRecord.model_validate_json(
            json.dumps({**row, "completed_check_ids": ["modelscan"]})
        )


def test_coverage_schema_snapshot() -> None:
    expected = json.loads((Path(__file__).parents[1] / "schemas/coverage-v1.json").read_text())
    assert CoverageRecord.model_json_schema() == expected
