"""Bounded comparisons of stored assertions; no policy evaluation or raw-file reads."""

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Annotated, Any, Literal, Self

from pydantic import Field, model_validator

from modelvet.core.errors import InvalidInput
from modelvet.evidence.models import SHA256, ArtifactDigest, CheckStatus, WireModel
from modelvet.inventory.classify import FileFormat
from modelvet.policies.models import CHECK_IDS, DecisionState
from modelvet.reports.json_report import parse_report, read_report_bytes, semantic_content

MAX_CHANGES = 200


class FileDifference(WireModel):
    path_digest: SHA256
    relpath: str | None
    kind: Literal["ADDED", "REMOVED", "CHANGED"]
    before_sha256: SHA256 | None
    after_sha256: SHA256 | None
    before_format: FileFormat | None
    after_format: FileFormat | None
    before_mismatch: bool | None
    after_mismatch: bool | None


class CheckDifference(WireModel):
    path_digest: SHA256
    relpath: str | None
    check_id: str
    before_observations: int
    after_observations: int
    before_statuses: tuple[CheckStatus, ...]
    after_statuses: tuple[CheckStatus, ...]


class ReportComparison(WireModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    before_report_sha256: SHA256
    after_report_sha256: SHA256
    before_artifact: ArtifactDigest
    after_artifact: ArtifactDigest
    before_policy: ArtifactDigest
    after_policy: ArtifactDigest
    before_semantic: ArtifactDigest
    after_semantic: ArtifactDigest
    stored_decision_before: DecisionState
    stored_decision_after: DecisionState
    same_report_bytes: bool
    same_artifact: bool
    same_policy: bool
    same_semantics: bool
    same_declared_raw: bool
    changed_sections: tuple[str, ...]
    changed_file_count: Annotated[int, Field(ge=0)]
    changed_check_count: Annotated[int, Field(ge=0)]
    omitted_file_changes: Annotated[int, Field(ge=0)]
    omitted_check_changes: Annotated[int, Field(ge=0)]
    files: Annotated[tuple[FileDifference, ...], Field(max_length=MAX_CHANGES)]
    checks: Annotated[tuple[CheckDifference, ...], Field(max_length=MAX_CHANGES)]
    admission_recomputed: Literal[False] = False
    notice: Literal[
        "Stored assertions; raw bytes and authors are not authenticated. No admission recomputed."
    ] = "Stored assertions; raw bytes and authors are not authenticated. No admission recomputed."

    @model_validator(mode="after")
    def consistent(self) -> Self:
        if (
            self.same_report_bytes != (self.before_report_sha256 == self.after_report_sha256)
            or self.same_artifact != (self.before_artifact == self.after_artifact)
            or self.same_policy != (self.before_policy == self.after_policy)
            or self.same_semantics != (self.before_semantic == self.after_semantic)
            or self.same_semantics != (not self.changed_sections)
            or self.changed_file_count != len(self.files) + self.omitted_file_changes
            or self.changed_check_count != len(self.checks) + self.omitted_check_changes
        ):
            raise ValueError("Comparison identities, counts or semantic indicators disagree.")
        return self


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def compare_reports(
    before: Path, after: Path, *, show_paths: bool = False, max_changes: int = MAX_CHANGES
) -> ReportComparison:
    if type(max_changes) is not int or not 0 <= max_changes <= MAX_CHANGES:
        raise InvalidInput("Comparison row limit must be within 0–200.")
    old_bytes, new_bytes = read_report_bytes(before), read_report_bytes(after)
    old, new = parse_report(old_bytes), parse_report(new_bytes)
    old_semantic = semantic_content(old.model_dump(mode="json"))
    new_semantic = semantic_content(new.model_dump(mode="json"))
    sections = tuple(sorted(k for k in old_semantic if old_semantic[k] != new_semantic[k]))
    old_files = {f.relpath: f for f in old.files}
    new_files = {f.relpath: f for f in new.files}
    file_rows: list[FileDifference] = []
    file_count = 0
    for path in sorted(old_files.keys() | new_files.keys()):
        left, right = old_files.get(path), new_files.get(path)
        signature_left = (
            (left.sha256, left.size, left.format_class, left.mismatch) if left else None
        )
        signature_right = (
            (right.sha256, right.size, right.format_class, right.mismatch) if right else None
        )
        if signature_left == signature_right:
            continue
        file_count += 1
        if len(file_rows) < max_changes:
            file_rows.append(
                FileDifference(
                    path_digest=hashlib.sha256(path.encode()).hexdigest(),
                    relpath=path if show_paths else None,
                    kind="ADDED" if left is None else "REMOVED" if right is None else "CHANGED",
                    before_sha256=left.sha256 if left else None,
                    after_sha256=right.sha256 if right else None,
                    before_format=left.format_class if left else None,
                    after_format=right.format_class if right else None,
                    before_mismatch=left.mismatch if left else None,
                    after_mismatch=right.mismatch if right else None,
                )
            )

    def checks_by_path(data: dict[str, Any]) -> dict[tuple[str, str], list[dict[str, Any]]]:
        names = {f["file_id"]: f["relpath"] for f in data["files"]}
        groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for check in data["checks"]:
            groups[(names[check["file_id"]], check["check_id"])].append(check)
        return groups

    old_checks, new_checks = checks_by_path(old_semantic), checks_by_path(new_semantic)
    check_rows: list[CheckDifference] = []
    check_count = 0
    for path, check_id in sorted(old_checks.keys() | new_checks.keys()):
        left_checks = old_checks.get((path, check_id), [])
        right_checks = new_checks.get((path, check_id), [])
        if sorted(map(_canonical, left_checks)) == sorted(map(_canonical, right_checks)):
            continue
        check_count += 1
        if len(check_rows) < max_changes:
            public_id = (
                check_id
                if check_id in CHECK_IDS
                else ("unrecognized:" + hashlib.sha256(check_id.encode()).hexdigest())
            )
            check_rows.append(
                CheckDifference(
                    path_digest=hashlib.sha256(path.encode()).hexdigest(),
                    relpath=path if show_paths else None,
                    check_id=public_id,
                    before_observations=len(left_checks),
                    after_observations=len(right_checks),
                    before_statuses=tuple(
                        CheckStatus(s) for s in sorted({c["status"] for c in left_checks})
                    ),
                    after_statuses=tuple(
                        CheckStatus(s) for s in sorted({c["status"] for c in right_checks})
                    ),
                )
            )
    if read_report_bytes(before) != old_bytes or read_report_bytes(after) != new_bytes:
        raise InvalidInput("Report changed during comparison.")
    return ReportComparison(
        before_report_sha256=hashlib.sha256(old_bytes).hexdigest(),
        after_report_sha256=hashlib.sha256(new_bytes).hexdigest(),
        before_artifact=old.manifest_digest,
        after_artifact=new.manifest_digest,
        before_policy=old.policy_digest,
        after_policy=new.policy_digest,
        before_semantic=old.semantic_digest,
        after_semantic=new.semantic_digest,
        stored_decision_before=old.decision.state,
        stored_decision_after=new.decision.state,
        same_report_bytes=old_bytes == new_bytes,
        same_artifact=old.manifest_digest == new.manifest_digest,
        same_policy=old.policy_digest == new.policy_digest,
        same_semantics=old.semantic_digest == new.semantic_digest,
        same_declared_raw=old.raw_evidence == new.raw_evidence,
        changed_sections=sections,
        changed_file_count=file_count,
        changed_check_count=check_count,
        omitted_file_changes=file_count - len(file_rows),
        omitted_check_changes=check_count - len(check_rows),
        files=tuple(file_rows),
        checks=tuple(check_rows),
    )
