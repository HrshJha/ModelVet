"""Admission precedence over independent checks, coverage and local facts."""

from collections import defaultdict

from modelvet.core.errors import InvalidInput
from modelvet.coverage.conflicts import ConflictDetector, check_reference
from modelvet.coverage.reconciler import CoverageReconciler, expectations_for
from modelvet.evidence.models import (
    CheckRecord,
    CheckResult,
    CheckStatus,
    ConflictRecord,
    CoverageRecord,
    Finding,
    MetadataClaim,
)
from modelvet.inventory.classify import FileClassification, FileFormat
from modelvet.inventory.discover import FileObservation
from modelvet.inventory.identity import ArtifactManifest, manifest_from_entries
from modelvet.policies.models import AdmissionDecision, DecisionState, Policy

MODEL_FORMATS = frozenset({FileFormat.SAFETENSORS, FileFormat.PICKLE_LIKE, FileFormat.PYTORCH_ZIP})
SERIALIZED_FORMATS = frozenset(
    {FileFormat.PICKLE_LIKE, FileFormat.PYTORCH_ZIP, FileFormat.ZIP_OTHER}
)


def _coverage_key(row: CoverageRecord) -> tuple[object, ...]:
    return (
        row.file_id,
        *(
            tuple(sorted(getattr(row, field)))
            for field in (
                "expected_check_ids",
                "mandatory_check_ids",
                "completed_check_ids",
                "skipped_check_ids",
                "failed_check_ids",
                "unsupported_check_ids",
                "inconclusive_check_ids",
                "not_run_check_ids",
                "nonapplicable_check_ids",
            )
        ),
    )


class AdmissionEvaluator:
    def evaluate(
        self,
        policy: Policy,
        manifest: ArtifactManifest,
        coverage: list[CoverageRecord],
        findings: list[Finding],
        conflicts: list[ConflictRecord],
        *,
        classifications: dict[str, FileClassification],
        checks: list[CheckRecord],
        claims: list[MetadataClaim],
    ) -> AdmissionDecision:
        """Typed inputs come from owned inventory/normalization, never scanner assertions.

        Reconcile again so a missing/tampered coverage row cannot erase a predicate.
        No human exception or free-form expression is evaluated in v1.
        """
        reasons: set[str] = set()
        refs: set[str] = set()

        def decision(
            state: DecisionState, rules: set[str], evidence: set[str]
        ) -> AdmissionDecision:
            descriptions = {
                DecisionState.BLOCK: "Inventory evidence substantiates a policy prohibition.",
                DecisionState.INSUFFICIENT: "Required evidence is incomplete or unresolved.",
                DecisionState.CONTROLS: "Required checks completed; named conditions apply.",
                DecisionState.APPROVE: (
                    "Configured static checks completed for this artifact and policy; "
                    "scoped approval only."
                ),
            }
            controls = (
                tuple(
                    sorted(
                        (c for c in policy.controls if c.control_id in selected_controls),
                        key=lambda c: c.control_id,
                    )
                )
                if state == DecisionState.CONTROLS
                else ()
            )
            return AdmissionDecision(
                state=state,
                rule_ids=tuple(sorted(rules)),
                reason=descriptions[state],
                evidence_refs=tuple(sorted(evidence)),
                required_controls=controls,
            )

        selected_controls: set[str] = set()
        try:
            canonical = manifest_from_entries(
                tuple(FileObservation(f.relpath, f.size, f.sha256) for f in manifest.files)
            )
            if canonical != manifest:
                raise InvalidInput("Manifest identity is inconsistent.")
            expected = expectations_for(
                manifest, classifications, frozenset(policy.mandatory_checks)
            )
            reconciled = CoverageReconciler().reconcile(manifest, expected, checks)
        except InvalidInput:
            return decision(DecisionState.INSUFFICIENT, {"INVALID-EVIDENCE"}, set())

        files = {f.file_id: f for f in manifest.files}
        observed: dict[tuple[str, str], list[CheckRecord]] = defaultdict(list)
        for check in checks:
            observed[(check.file_id, check.check_id)].append(check)
        supplied: dict[str, list[CoverageRecord]] = defaultdict(list)
        for row in coverage:
            supplied[row.file_id].append(row)
        coverage_valid: set[str] = set()
        for row in reconciled:
            candidates = supplied.get(row.file_id, [])
            if len(candidates) == 1 and _coverage_key(candidates[0]) == _coverage_key(row):
                coverage_valid.add(row.file_id)
            else:
                reasons.add("INVALID-EVIDENCE")
                refs.add("file:" + row.file_id)
            if row.mandatory_unresolved:
                reasons.add("MISSING-MANDATORY")
                refs.update(f"coverage:{row.file_id}:{check}" for check in row.mandatory_unresolved)
        if set(supplied) - files.keys() or set(classifications) != files.keys():
            reasons.add("INVALID-EVIDENCE")

        all_conflicts = [
            *conflicts,
            *ConflictDetector().detect(claims, checks, manifest, frozenset(policy.required_claims)),
        ]
        relevant = [
            c
            for c in all_conflicts
            if c.decision_relevant
            or c.type in policy.required_claims
            or c.type in {"IDENTITY", "CHECK_STATUS", "EVIDENCE_ID"}
        ]
        if relevant:
            reasons.add("UNRESOLVED-CONFLICT")
            refs.update("conflict:" + c.conflict_id for c in relevant)

        # Find which files are contradicted; an unbound integrity conflict taints every ban proof.
        check_files = {check_reference(c): c.file_id for c in checks}
        claim_files = {c.claim_id: c.source_file_id for c in claims}
        tainted: set[str] = set()
        for conflict in relevant:
            affected = {check_files[r] for r in conflict.check_refs if r in check_files}
            affected.update(claim_files[r] for r in conflict.claim_ids if r in claim_files)
            if conflict.subject in files:
                affected.add(conflict.subject)
            if conflict.type in {"IDENTITY", "CHECK_STATUS", "EVIDENCE_ID"}:
                tainted.update(affected or files.keys())

        def proof(file_id: str, check_id: str) -> CheckRecord | None:
            records = observed[(file_id, check_id)]
            if len(records) != 1:
                return None
            check = records[0]
            executor = "modelscan" if check_id in {"modelscan", "scanner:resources"} else "modelvet"
            if (
                check.status != CheckStatus.COMPLETE
                or check.artifact_digest != manifest.manifest_digest
                or check.executor_id != executor
                or check.error_code is not None
            ):
                return None
            return check

        ban_refs: set[str] = set()
        ban_rules: set[str] = set()
        has_model = False
        conditions: set[str] = set()
        for file in manifest.files:
            kind = classifications.get(file.file_id)
            identity = proof(file.file_id, "identity")
            classification = proof(file.file_id, "classification")
            facts_valid = (
                identity is not None
                and identity.details.get("sha256") == file.sha256
                and classification is not None
                and kind is not None
                and classification.details.get("format_class") == kind.format_class.value
                and classification.details.get("mismatch") is kind.mismatch
            )
            if not facts_valid:
                reasons.add("INVALID-EVIDENCE")
                refs.add("file:" + file.file_id)
            if (
                kind is None
                or kind.mismatch
                or kind.format_class in {FileFormat.UNKNOWN, FileFormat.BINARY_UNKNOWN}
            ):
                reasons.add("UNSUPPORTED-FORMAT")
                refs.add("file:" + file.file_id)
            if kind is None:
                continue
            has_model |= kind.format_class in MODEL_FORMATS
            if kind.format_class in MODEL_FORMATS:
                conditions.add("MODEL_PRESENT")
            if kind.format_class in SERIALIZED_FORMATS:
                conditions.add("SERIALIZED_MODEL")
            if kind.format_class == FileFormat.PYTHON_SOURCE:
                conditions.add("REPOSITORY_CODE")
                presence = proof(file.file_id, "source:presence")
                source_required = (
                    "source:presence" in policy.mandatory_checks
                    or bool(policy.prohibitions)
                    or any(r.condition == "REPOSITORY_CODE" for r in policy.control_rules)
                )
                if source_required and (
                    presence is None or presence.details.get("source_present") is not True
                ):
                    reasons.add("INVALID-EVIDENCE")
                    refs.add("file:" + file.file_id)
                if (
                    facts_valid
                    and not kind.mismatch
                    and presence is not None
                    and presence.details.get("source_present") is True
                    and file.file_id in coverage_valid
                    and file.file_id not in tainted
                ):
                    for rule in policy.prohibitions:
                        if rule.category == "REPOSITORY_CODE":
                            ban_rules.add(rule.rule_id)
                            ban_refs.update(
                                check_reference(c)
                                for c in (identity, classification, presence)
                                if c is not None
                            )

        if ban_rules:
            return decision(DecisionState.BLOCK, ban_rules, ban_refs)
        if not has_model:
            reasons.add("NO-MODEL")
        for row in reconciled:
            for check_id in set(row.mandatory_check_ids) & set(row.completed_check_ids):
                if proof(row.file_id, check_id) is None:
                    reasons.add("INVALID-EVIDENCE")
                    refs.add(f"coverage:{row.file_id}:{check_id}")
        for claim_kind in policy.required_claims:
            claim_candidates = [c for c in claims if c.kind == claim_kind]
            if not any(
                c.source_file_id in files
                and files[c.source_file_id].sha256 == c.source_sha256
                and proof(
                    c.source_file_id,
                    "dependencies:declared" if claim_kind == "DEPENDENCY" else "metadata:local",
                )
                for c in claim_candidates
            ):
                reasons.add("MISSING-CLAIM")
                refs.add("claim-kind:" + claim_kind)

        # V1 has no independent malicious-operation adjudicator. A severity or
        # CORROBORATED label alone never proves a policy ban or a clean assessment.
        for claim in claims:
            if claim.kind == "PROVENANCE" and claim.value in {
                "trust_remote_code=true",
                "custom_loader_mapping_declared",
            }:
                reasons.add("UNRESOLVED-FINDING")
                refs.add("claim:" + claim.claim_id)
        for finding in findings:
            reasons.add("UNRESOLVED-FINDING")
            refs.add("finding:" + finding.finding_id)
        for check in checks:
            if check.result == CheckResult.FINDINGS:
                reasons.add("UNRESOLVED-FINDING")
                refs.add(check_reference(check))
        if reasons:
            return decision(DecisionState.INSUFFICIENT, reasons, refs)
        control_rules = {
            rule.rule_id for rule in policy.control_rules if rule.condition in conditions
        }
        for control_rule in policy.control_rules:
            if control_rule.rule_id in control_rules:
                selected_controls.update(control_rule.control_ids)
        if control_rules:
            return decision(DecisionState.CONTROLS, control_rules, {manifest.manifest_digest})
        return decision(DecisionState.APPROVE, {"POLICY-APPROVE"}, {manifest.manifest_digest})
