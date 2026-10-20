"""Preserve differing declarations and assessment contradictions without choosing a winner."""

import hashlib
import json
from collections import defaultdict

from modelvet.evidence.models import CheckRecord, ConflictRecord, ConflictType, MetadataClaim
from modelvet.inventory.identity import ArtifactManifest


def check_reference(check: CheckRecord) -> str:
    # Raw observation timestamps/log hashes do not change this semantic reference.
    content = json.dumps(
        check.model_dump(mode="json", exclude={"raw_ref"}),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return "check:" + hashlib.sha256(content.encode()).hexdigest()


def _conflict(
    kind: ConflictType,
    subject: str,
    reason: str,
    relevant: bool,
    claims: tuple[str, ...] = (),
    checks: tuple[str, ...] = (),
) -> ConflictRecord:
    claims = tuple(sorted(set(claims)))
    checks = tuple(sorted(set(checks)))
    fingerprint = hashlib.sha256(
        json.dumps([kind, subject, claims, checks], sort_keys=True).encode()
    ).hexdigest()
    return ConflictRecord(
        conflict_id=fingerprint,
        type=kind,
        subject=subject,
        reason=reason,
        decision_relevant=relevant,
        claim_ids=claims,
        check_refs=checks,
    )


class ConflictDetector:
    def detect(
        self,
        claims: list[MetadataClaim],
        checks: list[CheckRecord],
        manifest: ArtifactManifest,
        required_claim_kinds: frozenset[str] = frozenset(),
    ) -> list[ConflictRecord]:
        files = {file.file_id: file for file in manifest.files}
        output: list[ConflictRecord] = []
        grouped: dict[tuple[ConflictType, str], list[MetadataClaim]] = defaultdict(list)
        ids: dict[str, list[MetadataClaim]] = defaultdict(list)
        for claim in claims:
            ids[claim.claim_id].append(claim)
            file = files.get(claim.source_file_id)
            if file is None or file.sha256 != claim.source_sha256:
                output.append(
                    _conflict(
                        "IDENTITY",
                        claim.source_file_id,
                        "Claim source identity does not match the manifest.",
                        True,
                        (claim.claim_id,),
                    )
                )
            subject = claim.value.partition("=")[0] if claim.kind != "LICENSE" else "license"
            grouped[(claim.kind, subject)].append(claim)
        for claim_id, items in ids.items():
            if len({item.model_dump_json() for item in items}) > 1:
                output.append(
                    _conflict(
                        "EVIDENCE_ID",
                        claim_id,
                        "One claim ID identifies differing statements.",
                        True,
                        (claim_id,),
                    )
                )
        for (kind, subject), items in grouped.items():
            if len({item.value for item in items}) > 1:
                output.append(
                    _conflict(
                        kind,
                        subject,
                        "Different local declarations are preserved; no automatic resolution.",
                        kind in required_claim_kinds,
                        tuple(item.claim_id for item in items),
                    )
                )
        observations: dict[tuple[str, str], list[CheckRecord]] = defaultdict(list)
        for check in checks:
            reference = check_reference(check)
            observations[(check.file_id, check.check_id)].append(check)
            if (
                check.file_id not in files
                or check.artifact_digest != manifest.manifest_digest
                or check.error_code == "SCANNER_IDENTITY_MISMATCH"
            ):
                output.append(
                    _conflict(
                        "IDENTITY",
                        check.file_id,
                        "Assessment source identity is inconsistent.",
                        True,
                        checks=(reference,),
                    )
                )
            if check.error_code == "SCANNER_COVERAGE_CONFLICT":
                output.append(
                    _conflict(
                        "CHECK_STATUS",
                        check.file_id,
                        "Scanner reports both assessed and skipped content.",
                        True,
                        checks=(reference,),
                    )
                )
        for (file_id, check_id), check_items in observations.items():
            if len(check_items) > 1:
                output.append(
                    _conflict(
                        "CHECK_STATUS",
                        f"{file_id}:{check_id}",
                        "Duplicate or differing observations are not resolved by list order.",
                        True,
                        checks=tuple(check_reference(item) for item in check_items),
                    )
                )
        return sorted(
            {item.conflict_id: item for item in output}.values(), key=lambda item: item.conflict_id
        )
