import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from modelvet.coverage.conflicts import ConflictDetector, check_reference
from modelvet.evidence.models import (
    CheckRecord,
    CheckResult,
    CheckStatus,
    ConflictRecord,
    MetadataClaim,
)
from modelvet.inventory.discover import FileObservation
from modelvet.inventory.identity import manifest_from_entries


def fixture():
    return manifest_from_entries(
        tuple(
            FileObservation(name, 1, hashlib.sha256(b"x").hexdigest())
            for name in ("README.md", "config.json")
        )
    )


def claim(file, value: str, kind="LICENSE") -> MetadataClaim:
    reference = file.file_id + "#declaration"
    return MetadataClaim(
        claim_id=hashlib.sha256((reference + value).encode()).hexdigest(),
        kind=kind,
        value=value,
        source_ref=reference,
        source_file_id=file.file_id,
        source_sha256=file.sha256,
    )


def check(manifest, status: CheckStatus = CheckStatus.COMPLETE) -> CheckRecord:
    return CheckRecord(
        check_id="modelscan",
        file_id=manifest.files[0].file_id,
        executor_id="modelscan",
        status=status,
        result=CheckResult.NO_FINDINGS if status == CheckStatus.COMPLETE else CheckResult.UNKNOWN,
        artifact_digest=manifest.manifest_digest,
    )


def test_consistent_claims_have_no_conflict() -> None:
    manifest = fixture()
    assert (
        ConflictDetector().detect([claim(file, "MIT") for file in manifest.files], [], manifest)
        == []
    )


def test_opposing_licenses_preserved_and_policy_relevant() -> None:
    manifest = fixture()
    claims = [claim(manifest.files[0], "Apache-2.0"), claim(manifest.files[1], "CC-BY-NC")]
    first = ConflictDetector().detect(claims, [], manifest)
    required = ConflictDetector().detect(claims, [], manifest, frozenset({"LICENSE"}))
    assert set(first[0].claim_ids) == {item.claim_id for item in claims}
    assert not first[0].decision_relevant and required[0].decision_relevant
    assert ConflictDetector().detect(list(reversed(claims)), [], manifest) == first
    assert [item.value for item in claims] == ["Apache-2.0", "CC-BY-NC"]


def test_distinct_provenance_fields_are_not_conflicting() -> None:
    manifest = fixture()
    claims = [
        claim(manifest.files[0], "repo_id=org/model", "PROVENANCE"),
        claim(manifest.files[1], "revision=abc", "PROVENANCE"),
    ]
    assert ConflictDetector().detect(claims, [], manifest) == []
    claims.append(claim(manifest.files[0], "revision=other", "PROVENANCE"))
    result = ConflictDetector().detect(claims, [], manifest, frozenset({"PROVENANCE"}))
    assert len(result) == 1 and result[0].subject == "revision" and result[0].decision_relevant


def test_claim_identity_and_duplicate_id_conflicts() -> None:
    manifest = fixture()
    original = claim(manifest.files[0], "MIT")
    changed = original.model_copy(update={"value": "other", "source_sha256": "f" * 64})
    result = ConflictDetector().detect([original, changed], [], manifest)
    assert {"IDENTITY", "EVIDENCE_ID"} <= {item.type for item in result}
    assert all(
        item.decision_relevant for item in result if item.type in {"IDENTITY", "EVIDENCE_ID"}
    )


def test_check_contradictions_independent_of_order() -> None:
    manifest = fixture()
    checks = [check(manifest), check(manifest, CheckStatus.FAILED)]
    result = ConflictDetector().detect([], checks, manifest)
    assert result == ConflictDetector().detect([], list(reversed(checks)), manifest)
    assert result[0].decision_relevant
    assert set(result[0].check_refs) == {check_reference(item) for item in checks}


def test_single_normalized_scanner_contradiction() -> None:
    manifest = fixture()
    record = check(manifest, CheckStatus.INCONCLUSIVE).model_copy(
        update={"error_code": "SCANNER_COVERAGE_CONFLICT"}
    )
    result = ConflictDetector().detect([], [record], manifest)
    assert result[0].type == "CHECK_STATUS" and result[0].decision_relevant


def test_wrong_check_artifact_is_identity_conflict() -> None:
    manifest = fixture()
    record = check(manifest).model_copy(update={"artifact_digest": "sha256:" + "f" * 64})
    assert ConflictDetector().detect([], [record], manifest)[0].type == "IDENTITY"


def test_unattributed_conflict_rejected() -> None:
    with pytest.raises(ValidationError):
        ConflictRecord(
            conflict_id="0" * 64, type="LICENSE", decision_relevant=True, reason="no source"
        )


def test_conflict_schema_snapshot() -> None:
    expected = json.loads((Path(__file__).parents[1] / "schemas/conflict-v1.json").read_text())
    assert ConflictRecord.model_json_schema() == expected
