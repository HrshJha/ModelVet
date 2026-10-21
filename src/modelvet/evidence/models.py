"""Strict v1 evidence types. Execution, result and verification remain distinct."""

import math
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator, model_validator

SHA256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
ArtifactDigest = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
Identifier = Annotated[str, Field(min_length=1, max_length=256)]
ExecutionStatus = Literal["COMPLETE", "FAILED", "NOT_RUN", "INCONCLUSIVE"]
ConflictType = Literal[
    "LICENSE", "PROVENANCE", "DEPENDENCY", "IDENTITY", "CHECK_STATUS", "EVIDENCE_ID"
]


class WireModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, allow_inf_nan=False)


def _finite_json(value: JsonValue | tuple[JsonValue, ...]) -> None:
    pending = [(value, 0)]
    count = 0
    while pending:
        item, depth = pending.pop()
        count += 1
        if depth > 64 or count > 100_000:
            raise ValueError("Normalized JSON exceeds structural limits.")
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError("Nonfinite normalized JSON value.")
        if isinstance(item, str):
            item.encode("utf-8", errors="strict")
        elif isinstance(item, dict):
            for key, child in item.items():
                key.encode("utf-8", errors="strict")
                pending.append((child, depth + 1))
        elif isinstance(item, (list, tuple)):
            pending.extend((child, depth + 1) for child in item)


class CheckStatus(StrEnum):
    COMPLETE = "COMPLETE"
    SKIPPED = "SKIPPED"
    FAILED = "FAILED"
    UNSUPPORTED = "UNSUPPORTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_RUN = "NOT_RUN"


class CheckResult(StrEnum):
    FINDINGS = "FINDINGS"
    NO_FINDINGS = "NO_FINDINGS"
    UNKNOWN = "UNKNOWN"


class Severity(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"
    UNKNOWN = "UNKNOWN"


class FindingVerification(StrEnum):
    REPORTED = "REPORTED"
    CORROBORATED = "CORROBORATED"
    DISPUTED = "DISPUTED"


class ToolInfo(WireModel):
    tool_id: Identifier
    version: Identifier
    source: str
    binary_sha256: SHA256 | None = None


class ToolExecution(WireModel):
    execution_id: Identifier
    tool_id: Identifier
    status: ExecutionStatus
    artifact_digest: ArtifactDigest
    exit_code: int | None = None
    started_at: str | None = None
    ended_at: str | None = None
    stdout_digest: SHA256 | None = None
    stderr_digest: SHA256 | None = None
    raw_report_digest: SHA256 | None = None
    environment_digest: SHA256 | None = None
    reason: str | None = None
    limitations: tuple[str, ...] = ()

    @field_validator("started_at", "ended_at")
    @classmethod
    def utc_timestamp(cls, value: str | None) -> str | None:
        if value is not None:
            parsed = datetime.fromisoformat(value)
            if (
                "T" not in value
                or not value.endswith(("Z", "+00:00"))
                or parsed.utcoffset() != timedelta(0)
            ):
                raise ValueError("Timestamp must use UTC RFC3339.")
        return value


class CheckRecord(WireModel):
    check_id: Identifier
    file_id: SHA256
    executor_id: Identifier
    status: CheckStatus
    result: CheckResult
    artifact_digest: ArtifactDigest
    normalizer_version: Literal["1"] = "1"
    raw_ref: ArtifactDigest | None = None
    reason: Annotated[str, Field(max_length=2048)] | None = None
    error_code: Identifier | None = None
    details: dict[str, JsonValue] = Field(default_factory=dict)
    limitations: tuple[str, ...] = ()

    @field_validator("details")
    @classmethod
    def finite_details(cls, value: dict[str, JsonValue]) -> dict[str, JsonValue]:
        _finite_json(value)
        return value

    @model_validator(mode="after")
    def consistent_result(self) -> Self:
        if (self.status == CheckStatus.COMPLETE) == (self.result == CheckResult.UNKNOWN):
            raise ValueError(
                "Only complete checks may have a known result; complete needs a result."
            )
        return self


class Finding(WireModel):
    finding_id: SHA256
    file_id: SHA256
    check_id: Identifier
    category: Identifier
    severity: Severity
    verification_state: FindingVerification
    source_ref: Annotated[str, Field(max_length=2048)]
    description: Annotated[str, Field(max_length=4096)] = ""
    location: str | None = None
    related_cve: str | None = None
    rule_id: str | None = None


class MetadataClaim(WireModel):
    claim_id: SHA256
    kind: Literal["LICENSE", "PROVENANCE", "DEPENDENCY"]
    value: Annotated[str, Field(min_length=1, max_length=4096)]
    source_ref: str
    source_file_id: SHA256
    source_sha256: SHA256
    source_line: Annotated[int, Field(ge=1)] | None = None
    confidence: Literal["DECLARED", "INFERRED", "HUMAN_REVIEWED"] = "DECLARED"


class DependencyRecord(WireModel):
    name: Identifier
    ecosystem: Identifier
    version: str | None
    source_ref: str
    source_sha256: SHA256
    status: Literal["DECLARED_PINNED", "INCONCLUSIVE"]
    reason: str | None = None
    advisories: tuple[JsonValue, ...] | None = None

    @field_validator("advisories")
    @classmethod
    def finite_advisories(cls, value: tuple[JsonValue, ...] | None) -> tuple[JsonValue, ...] | None:
        if value is not None:
            _finite_json(value)
        return value


class EvidenceBundle(WireModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    tools: tuple[ToolInfo, ...] = ()
    executions: tuple[ToolExecution, ...] = ()
    checks: tuple[CheckRecord, ...] = ()
    findings: tuple[Finding, ...] = ()
    claims: tuple[MetadataClaim, ...] = ()
    dependencies: tuple[DependencyRecord, ...] = ()
    limitations: tuple[str, ...] = ()


class ExpectedCheck(WireModel):
    file_id: SHA256
    check_id: Identifier
    mandatory: bool = True


class CoverageRecord(WireModel):
    file_id: SHA256
    expected_check_ids: tuple[Identifier, ...]
    mandatory_check_ids: tuple[Identifier, ...] = ()
    completed_check_ids: tuple[Identifier, ...] = ()
    skipped_check_ids: tuple[Identifier, ...] = ()
    failed_check_ids: tuple[Identifier, ...] = ()
    unsupported_check_ids: tuple[Identifier, ...] = ()
    inconclusive_check_ids: tuple[Identifier, ...] = ()
    not_run_check_ids: tuple[Identifier, ...] = ()
    unresolved_reasons: tuple[str, ...] = ()
    nonapplicable_check_ids: tuple[Identifier, ...] = ()

    @model_validator(mode="after")
    def complete_partition(self) -> Self:
        expected = set(self.expected_check_ids)
        buckets = (
            self.completed_check_ids,
            self.skipped_check_ids,
            self.failed_check_ids,
            self.unsupported_check_ids,
            self.inconclusive_check_ids,
            self.not_run_check_ids,
        )
        seen: set[str] = set()
        for bucket in buckets:
            if len(set(bucket)) != len(bucket) or seen.intersection(bucket):
                raise ValueError("Coverage states must be disjoint and unique.")
            seen.update(bucket)
        if (
            seen != expected
            or len(expected) != len(self.expected_check_ids)
            or not set(self.mandatory_check_ids) <= expected
            or set(self.nonapplicable_check_ids) & expected
        ):
            raise ValueError("Coverage must account for every applicable pair exactly once.")
        return self

    @property
    def mandatory_unresolved(self) -> tuple[str, ...]:
        return tuple(sorted(set(self.mandatory_check_ids) - set(self.completed_check_ids)))


class ConflictRecord(WireModel):
    conflict_id: SHA256
    type: ConflictType
    claim_ids: tuple[SHA256, ...] = ()
    check_refs: tuple[Identifier, ...] = ()
    decision_relevant: bool
    reason: Annotated[str, Field(min_length=1, max_length=2048)]
    subject: Identifier | None = None
    resolution_ref: str | None = None

    @model_validator(mode="after")
    def attributable(self) -> Self:
        if not self.claim_ids and not self.check_refs:
            raise ValueError("A conflict must reference its source evidence.")
        return self
