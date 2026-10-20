"""Join expectations to observations; absence and disagreement cannot complete checks."""

from collections import defaultdict

from modelvet.core.errors import InvalidInput
from modelvet.evidence.models import CheckRecord, CheckStatus, CoverageRecord, ExpectedCheck
from modelvet.inventory.classify import FileClassification, FileFormat, applicable_checks
from modelvet.inventory.identity import ArtifactManifest


def expectations_for(
    manifest: ArtifactManifest,
    classifications: dict[str, FileClassification],
    mandatory_check_ids: frozenset[str] | None = None,
) -> list[ExpectedCheck]:
    """Use the independent registry, never scanner-provided check/file counts."""
    expected: list[ExpectedCheck] = []
    for file in manifest.files:
        classification = classifications.get(file.file_id)
        kind = classification.format_class if classification else FileFormat.UNKNOWN
        ids = applicable_checks(kind)
        if file.relpath == "modelvet-environment.json":
            ids += ("dependencies:declared",)
        for check_id in ids:
            required = (
                mandatory_check_ids is None
                or check_id in mandatory_check_ids
                or check_id in {"identity", "classification"}
            )
            expected.append(
                ExpectedCheck(file_id=file.file_id, check_id=check_id, mandatory=required)
            )
    return expected


class CoverageReconciler:
    def reconcile(
        self,
        manifest: ArtifactManifest,
        expectations: list[ExpectedCheck],
        evidence: list[CheckRecord],
    ) -> list[CoverageRecord]:
        file_ids = {file.file_id for file in manifest.files}
        expected: dict[tuple[str, str], ExpectedCheck] = {}
        by_file: dict[str, list[tuple[str, ExpectedCheck]]] = defaultdict(list)
        for item in expectations:
            key = (item.file_id, item.check_id)
            if item.file_id not in file_ids or key in expected:
                raise InvalidInput("Unknown file or duplicate coverage expectation.")
            expected[key] = item
            by_file[item.file_id].append((item.check_id, item))
        observations: dict[tuple[str, str], list[CheckRecord]] = defaultdict(list)
        observed_ids: dict[str, set[str]] = defaultdict(set)
        for record in evidence:
            if record.file_id not in file_ids:
                raise InvalidInput("Evidence references a file outside the manifest.")
            observations[(record.file_id, record.check_id)].append(record)
            observed_ids[record.file_id].add(record.check_id)
        result: list[CoverageRecord] = []
        for file in manifest.files:
            pairs = sorted(by_file[file.file_id])
            states: dict[CheckStatus, list[str]] = {status: [] for status in CheckStatus}
            reasons: list[str] = []
            for check_id, _ in pairs:
                records = observations.get((file.file_id, check_id), [])
                reason = None
                if not records:
                    status = CheckStatus.INCONCLUSIVE
                    reason = "No positive assessment evidence."
                elif len(records) != 1:
                    status = CheckStatus.INCONCLUSIVE
                    reason = "Duplicate or conflicting observations require reconciliation."
                elif records[0].artifact_digest != manifest.manifest_digest:
                    status = CheckStatus.INCONCLUSIVE
                    reason = "Evidence artifact identity mismatch."
                else:
                    status = records[0].status
                    if status != CheckStatus.COMPLETE:
                        reason = f"Check status {status.value}."
                states[status].append(check_id)
                if reason:
                    reasons.append(f"{check_id}: {reason}")
            expected_ids = tuple(check_id for check_id, _ in pairs)
            extra = sorted(observed_ids[file.file_id] - set(expected_ids))
            result.append(
                CoverageRecord(
                    file_id=file.file_id,
                    expected_check_ids=expected_ids,
                    mandatory_check_ids=tuple(
                        check_id for check_id, item in pairs if item.mandatory
                    ),
                    completed_check_ids=tuple(states[CheckStatus.COMPLETE]),
                    skipped_check_ids=tuple(states[CheckStatus.SKIPPED]),
                    failed_check_ids=tuple(states[CheckStatus.FAILED]),
                    unsupported_check_ids=tuple(states[CheckStatus.UNSUPPORTED]),
                    inconclusive_check_ids=tuple(states[CheckStatus.INCONCLUSIVE]),
                    not_run_check_ids=tuple(states[CheckStatus.NOT_RUN]),
                    unresolved_reasons=tuple(reasons),
                    nonapplicable_check_ids=tuple(extra),
                )
            )
        return result
