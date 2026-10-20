"""T-POLICY-01: every status combination, independent bans and deterministic controls."""

import hashlib
from itertools import product

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from modelvet.coverage.reconciler import CoverageReconciler, expectations_for
from modelvet.evidence.models import (
    CheckRecord,
    CheckResult,
    CheckStatus,
    ConflictRecord,
    Finding,
    FindingVerification,
    MetadataClaim,
    Severity,
)
from modelvet.inventory.classify import FileClassification, FileFormat, applicable_checks
from modelvet.inventory.discover import FileObservation
from modelvet.inventory.identity import manifest_from_entries
from modelvet.policies.evaluator import AdmissionEvaluator
from modelvet.policies.models import (
    CHECK_IDS,
    AdmissionDecision,
    Control,
    ControlRule,
    DecisionState,
    Policy,
    Prohibition,
)


def policy(**updates) -> Policy:
    data = dict(
        schema_version="1.0.0",
        policy_id="test",
        policy_version="1",
        applicability_version="2",
        mandatory_checks=tuple(sorted(CHECK_IDS)),
        optional_checks=(),
        prohibitions=(Prohibition(rule_id="NO-SOURCE", category="REPOSITORY_CODE"),),
        controls=(),
        control_rules=(),
    )
    data.update(updates)
    return Policy(**data)


def fixture(*kinds: FileFormat):
    kinds = kinds or (FileFormat.SAFETENSORS,)
    manifest = manifest_from_entries(
        tuple(
            FileObservation(f"{i}.bin", 1, hashlib.sha256(bytes([i])).hexdigest())
            for i in range(len(kinds))
        )
    )
    classes = {
        f.file_id: FileClassification(kind, applicable_checks(kind))
        for f, kind in zip(manifest.files, kinds, strict=True)
    }
    checks = []
    for file in manifest.files:
        for check_id in classes[file.file_id].check_ids:
            details = {}
            if check_id == "identity":
                details = {"sha256": file.sha256}
            elif check_id == "classification":
                details = {
                    "format_class": classes[file.file_id].format_class.value,
                    "mismatch": False,
                }
            elif check_id == "source:presence":
                details = {"source_present": True}
            checks.append(
                CheckRecord(
                    file_id=file.file_id,
                    check_id=check_id,
                    executor_id="modelscan"
                    if check_id in {"modelscan", "scanner:resources"}
                    else "modelvet",
                    status=CheckStatus.COMPLETE,
                    result=CheckResult.NO_FINDINGS,
                    artifact_digest=manifest.manifest_digest,
                    details=details,
                )
            )
    return manifest, classes, checks


def evaluate(case, selected=None, *, rows=None, findings=(), conflicts=(), claims=()):
    manifest, classes, checks = case
    selected = selected or policy()
    if rows is None:
        rows = CoverageReconciler().reconcile(
            manifest,
            expectations_for(manifest, classes, frozenset(selected.mandatory_checks)),
            checks,
        )
    return AdmissionEvaluator().evaluate(
        selected,
        manifest,
        rows,
        list(findings),
        list(conflicts),
        classifications=classes,
        checks=checks,
        claims=list(claims),
    )


def controlled_policy() -> Policy:
    return policy(
        controls=(Control(control_id="ISOLATED_LOADING", owner="Deployment security"),),
        control_rules=(
            ControlRule(
                rule_id="ISOLATE", condition="MODEL_PRESENT", control_ids=("ISOLATED_LOADING",)
            ),
        ),
    )


def test_approve_and_named_controls() -> None:
    assert evaluate(fixture()).state == DecisionState.APPROVE
    decision = evaluate(fixture(), controlled_policy())
    assert decision.state == DecisionState.CONTROLS
    assert decision.required_controls[0].owner == "Deployment security"
    assert decision.rule_ids == ("ISOLATE",)


def test_exhaustive_mandatory_status_combinations() -> None:
    manifest, classes, checks = fixture(FileFormat.PICKLE_LIKE)
    for statuses in product(CheckStatus, repeat=4):
        observed = [
            check.model_copy(
                update={
                    "status": status,
                    "result": CheckResult.NO_FINDINGS
                    if status == CheckStatus.COMPLETE
                    else CheckResult.UNKNOWN,
                }
            )
            for check, status in zip(checks, statuses, strict=True)
        ]
        for selected in (policy(), controlled_policy()):
            result = evaluate((manifest, classes, observed), selected)
            if any(s != CheckStatus.COMPLETE for s in statuses):
                assert result.state == DecisionState.INSUFFICIENT
            else:
                assert result.state in {DecisionState.APPROVE, DecisionState.CONTROLS}


@given(st.lists(st.sampled_from(list(CheckStatus)), min_size=1, max_size=5))
def test_missing_or_duplicate_observations_cannot_promote(statuses) -> None:
    manifest, classes, checks = fixture()
    base = checks[-1]
    extras = [
        base.model_copy(
            update={
                "status": s,
                "result": CheckResult.NO_FINDINGS
                if s == CheckStatus.COMPLETE
                else CheckResult.UNKNOWN,
            }
        )
        for s in statuses
    ]
    first = evaluate((manifest, classes, checks[:-1] + extras))
    second = evaluate((manifest, classes, list(reversed(checks[:-1] + extras))))
    assert first == second
    if statuses != [CheckStatus.COMPLETE]:
        assert first.state == DecisionState.INSUFFICIENT


def test_independent_source_ban_precedes_unrelated_scanner_gap() -> None:
    manifest, classes, checks = fixture(FileFormat.PYTHON_SOURCE, FileFormat.PICKLE_LIKE)
    checks = [c for c in checks if c.check_id != "modelscan"]
    result = evaluate((manifest, classes, checks))
    assert result.state == DecisionState.BLOCK
    assert result.rule_ids == ("NO-SOURCE",)
    assert len(result.evidence_refs) == 3


@pytest.mark.parametrize("missing", ["identity", "classification", "source:presence"])
def test_ban_requires_its_own_complete_proof(missing) -> None:
    manifest, classes, checks = fixture(FileFormat.PYTHON_SOURCE, FileFormat.SAFETENSORS)
    source_id = manifest.files[0].file_id
    observed = [c for c in checks if (c.file_id, c.check_id) != (source_id, missing)]
    assert evaluate((manifest, classes, observed)).state == DecisionState.INSUFFICIENT


def test_ban_requires_source_fact_and_owned_executor() -> None:
    manifest, classes, checks = fixture(FileFormat.PYTHON_SOURCE, FileFormat.SAFETENSORS)
    for update in ({"details": {}}, {"executor_id": "modelscan"}):
        observed = [
            c.model_copy(update=update) if c.check_id == "source:presence" else c for c in checks
        ]
        assert evaluate((manifest, classes, observed)).state == DecisionState.INSUFFICIENT


def test_integrity_conflict_prevents_ban_but_unrelated_claim_does_not() -> None:
    case = fixture(FileFormat.PYTHON_SOURCE, FileFormat.SAFETENSORS)
    conflict = ConflictRecord(
        conflict_id="f" * 64,
        type="IDENTITY",
        check_refs=("unknown",),
        decision_relevant=True,
        reason="Identity drift.",
    )
    assert evaluate(case, conflicts=[conflict]).state == DecisionState.INSUFFICIENT
    unrelated = conflict.model_copy(update={"type": "LICENSE", "claim_ids": ("a" * 64,)})
    assert evaluate(case, conflicts=[unrelated]).state == DecisionState.BLOCK


def test_integrity_conflict_cannot_be_marked_irrelevant() -> None:
    conflict = ConflictRecord(
        conflict_id="f" * 64,
        type="IDENTITY",
        check_refs=("unknown",),
        decision_relevant=False,
        reason="Unbound identity drift.",
    )
    case = fixture(FileFormat.PYTHON_SOURCE, FileFormat.SAFETENSORS)
    assert evaluate(case, conflicts=[conflict]).state == DecisionState.INSUFFICIENT


def test_optional_source_gap_requires_explicitly_removed_prohibition() -> None:
    manifest, classes, checks = fixture(FileFormat.PYTHON_SOURCE, FileFormat.SAFETENSORS)
    observed = [c for c in checks if c.check_id != "source:presence"]
    optional = dict(
        mandatory_checks=tuple(sorted(CHECK_IDS - {"source:presence"})),
        optional_checks=("source:presence",),
    )
    assert (
        evaluate((manifest, classes, observed), policy(**optional)).state
        == DecisionState.INSUFFICIENT
    )
    assert (
        evaluate((manifest, classes, observed), policy(**optional, prohibitions=())).state
        == DecisionState.APPROVE
    )


@pytest.mark.parametrize("variant", ["missing", "duplicate", "unknown", "cleared", "promoted"])
def test_tampered_coverage_cannot_approve(variant) -> None:
    case = fixture()
    manifest, classes, checks = case
    rows = CoverageReconciler().reconcile(manifest, expectations_for(manifest, classes), checks)
    if variant == "missing":
        rows = []
    elif variant == "duplicate":
        rows += rows
    elif variant == "unknown":
        rows.append(rows[0].model_copy(update={"file_id": "f" * 64}))
    elif variant == "cleared":
        rows = [
            rows[0].model_copy(
                update={
                    "expected_check_ids": (),
                    "mandatory_check_ids": (),
                    "completed_check_ids": (),
                }
            )
        ]
    else:
        case = (manifest, classes, checks[:-1])
    assert evaluate(case, rows=rows).state == DecisionState.INSUFFICIENT


def test_empty_or_model_free_inventory_cannot_approve() -> None:
    empty = (manifest_from_entries(()), {}, [])
    assert evaluate(empty).state == DecisionState.INSUFFICIENT
    assert evaluate(fixture(FileFormat.JSON)).state == DecisionState.INSUFFICIENT


@pytest.mark.parametrize("kind", [FileFormat.UNKNOWN, FileFormat.BINARY_UNKNOWN])
def test_unknown_additional_file_cannot_hide_behind_clean_model(kind) -> None:
    assert evaluate(fixture(FileFormat.SAFETENSORS, kind)).state == DecisionState.INSUFFICIENT


def test_mismatch_missing_classification_and_wrong_identity() -> None:
    manifest, classes, checks = fixture()
    file_id = manifest.files[0].file_id
    mismatched = {file_id: FileClassification(FileFormat.SAFETENSORS, (), mismatch=True)}
    assert evaluate((manifest, mismatched, checks)).state == DecisionState.INSUFFICIENT
    assert evaluate((manifest, {}, checks)).state == DecisionState.INSUFFICIENT
    wrong = [c.model_copy(update={"artifact_digest": "sha256:" + "f" * 64}) for c in checks]
    assert evaluate((manifest, classes, wrong)).state == DecisionState.INSUFFICIENT
    forged = manifest.__class__("sha256:" + "f" * 64, manifest.files)
    assert evaluate((forged, classes, checks)).state == DecisionState.INSUFFICIENT


@pytest.mark.parametrize("verification", list(FindingVerification))
def test_scanner_label_or_severity_is_never_independent_ban(verification) -> None:
    case = fixture(FileFormat.PICKLE_LIKE)
    finding = Finding(
        finding_id="a" * 64,
        file_id=case[0].files[0].file_id,
        check_id="modelscan",
        category="REPOSITORY_CODE",
        severity=Severity.CRITICAL,
        verification_state=verification,
        source_ref="scanner:allegation",
    )
    assert evaluate(case, findings=[finding]).state == DecisionState.INSUFFICIENT


def test_findings_check_without_finding_records_is_unresolved() -> None:
    manifest, classes, checks = fixture()
    observed = [
        c.model_copy(update={"result": CheckResult.FINDINGS})
        if c.check_id.startswith("structural:")
        else c
        for c in checks
    ]
    assert evaluate((manifest, classes, observed)).state == DecisionState.INSUFFICIENT


def test_optional_gap_only_when_explicitly_allowed() -> None:
    optional = policy(
        mandatory_checks=tuple(sorted(CHECK_IDS - {"modelscan"})), optional_checks=("modelscan",)
    )
    manifest, classes, checks = fixture(FileFormat.PICKLE_LIKE)
    observed = [c for c in checks if c.check_id != "modelscan"]
    assert evaluate((manifest, classes, observed), optional).state == DecisionState.APPROVE
    assert evaluate((manifest, classes, observed)).state == DecisionState.INSUFFICIENT


def test_required_claims_need_sourced_complete_metadata_and_conflicts_stay_unresolved() -> None:
    manifest, classes, checks = fixture(FileFormat.SAFETENSORS, FileFormat.JSON)
    selected = policy(required_claims=("LICENSE",))
    assert evaluate((manifest, classes, checks), selected).state == DecisionState.INSUFFICIENT
    file = manifest.files[1]
    claim = MetadataClaim(
        claim_id="a" * 64,
        kind="LICENSE",
        value="MIT",
        source_ref="json:/license",
        source_file_id=file.file_id,
        source_sha256=file.sha256,
    )
    assert (
        evaluate((manifest, classes, checks), selected, claims=[claim]).state
        == DecisionState.APPROVE
    )
    conflicting = claim.model_copy(update={"claim_id": "b" * 64, "value": "Apache-2.0"})
    result = evaluate((manifest, classes, checks), selected, claims=[claim, conflicting])
    assert result.state == DecisionState.INSUFFICIENT
    assert "UNRESOLVED-CONFLICT" in result.rule_ids
    absent_metadata = [c for c in checks if c.check_id != "metadata:local"]
    assert (
        evaluate((manifest, classes, absent_metadata), selected, claims=[claim]).state
        == DecisionState.INSUFFICIENT
    )


def test_relevant_conflict_cannot_be_cleared_by_resolution_string() -> None:
    conflict = ConflictRecord(
        conflict_id="f" * 64,
        type="LICENSE",
        claim_ids=("a" * 64,),
        decision_relevant=True,
        reason="Conflicting declarations.",
        resolution_ref="approved",
    )
    assert (
        evaluate(fixture(), controlled_policy(), conflicts=[conflict]).state
        == DecisionState.INSUFFICIENT
    )


def test_permutations_are_byte_identical() -> None:
    manifest, classes, checks = fixture(FileFormat.PICKLE_LIKE, FileFormat.SAFETENSORS)
    rows = CoverageReconciler().reconcile(manifest, expectations_for(manifest, classes), checks)
    first = evaluate((manifest, classes, checks), controlled_policy(), rows=rows)
    second = evaluate(
        (manifest, dict(reversed(list(classes.items()))), list(reversed(checks))),
        controlled_policy(),
        rows=list(reversed(rows)),
    )
    assert first.model_dump_json() == second.model_dump_json()


def test_decision_schema_rejects_controls_without_owner_and_unattributed_block() -> None:
    for content in (
        dict(state="CONTROLS", required_controls=[]),
        dict(state="BLOCK", required_controls=[]),
    ):
        import json

        with pytest.raises(ValidationError):
            AdmissionDecision.model_validate_json(
                json.dumps({**content, "rule_ids": ["TEST"], "reason": "test", "evidence_refs": []})
            )
