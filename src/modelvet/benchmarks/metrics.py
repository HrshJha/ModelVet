"""Development counts only; absent reviewed positives never become a zero error rate."""

from collections import defaultdict
from typing import Annotated, Literal

from pydantic import Field, JsonValue, model_validator

from modelvet.core.errors import InvalidInput
from modelvet.evidence.models import ArtifactDigest, WireModel

Outcome = Literal[
    "COMPLETE_NO_FINDINGS",
    "REPORTED_FINDINGS",
    "POLICY_BLOCK",
    "UNRESOLVED",
    "UNAVAILABLE",
    "NOT_APPLICABLE",
]


class Observation(WireModel):
    fixture_id: str
    artifact_digest: ArtifactDigest
    tool_id: Literal["modelvet", "modelscan"]
    tool_version: str | None
    repeat_id: Annotated[int, Field(ge=1, le=3)]
    eligibility: Literal["SUPPORTED_CONTEXT", "NOT_APPLICABLE"]
    outcome: Outcome
    wall_s: Annotated[float, Field(ge=0)]
    peak_rss_bytes: Literal[None] = None
    decision: str | None = None
    evidence_ref: str | None = None
    raw_refs: tuple[ArtifactDigest, ...] = ()
    reason: str | None = None

    @model_validator(mode="after")
    def consistent(self) -> "Observation":
        if (self.eligibility == "NOT_APPLICABLE") != (self.outcome == "NOT_APPLICABLE"):
            raise ValueError("Not-applicable observations must remain outside metrics.")
        if self.outcome in {"COMPLETE_NO_FINDINGS", "REPORTED_FINDINGS", "POLICY_BLOCK"}:
            if self.tool_version is None or self.evidence_ref is None:
                raise ValueError("Assessed observations require versioned evidence.")
        if self.tool_id == "modelscan" and self.decision is not None:
            raise ValueError("Scanner status must not become an admission decision.")
        return self


def development_metrics(observations: tuple[Observation, ...]) -> dict[str, JsonValue]:
    seen = set()
    identities: dict[str, str] = {}
    grouped: dict[tuple[str, str], list[Observation]] = defaultdict(list)
    for row in observations:
        key = (row.fixture_id, row.tool_id, row.repeat_id)
        if key in seen:
            raise InvalidInput("Duplicate benchmark observation.")
        seen.add(key)
        if row.fixture_id in identities and identities[row.fixture_id] != row.artifact_digest:
            raise InvalidInput("Benchmark observations disagree on artifact identity.")
        identities[row.fixture_id] = row.artifact_digest
        grouped[(row.fixture_id, row.tool_id)].append(row)
    tools: dict[str, JsonValue] = {}
    for tool in ("modelvet", "modelscan"):
        rows = [r for r in observations if r.tool_id == tool]
        eligible = [r for r in rows if r.eligibility == "SUPPORTED_CONTEXT"]
        tools[tool] = {
            "observations": len(rows),
            "eligible_observations": len(eligible),
            "not_applicable": sum(r.eligibility == "NOT_APPLICABLE" for r in rows),
            "unavailable": sum(r.outcome == "UNAVAILABLE" for r in eligible),
            "unresolved": sum(r.outcome == "UNRESOLVED" for r in eligible),
            "complete_no_findings": sum(r.outcome == "COMPLETE_NO_FINDINGS" for r in eligible),
            "reported_findings": sum(r.outcome == "REPORTED_FINDINGS" for r in eligible),
            "policy_blocks": sum(r.outcome == "POLICY_BLOCK" for r in eligible),
            "wall_s_observed": [r.wall_s for r in eligible],
        }
    pair_keys = {
        (r.fixture_id, r.repeat_id)
        for r in observations
        if r.tool_id == "modelscan"
        and r.eligibility == "SUPPORTED_CONTEXT"
        and r.outcome != "UNAVAILABLE"
    } & {
        (r.fixture_id, r.repeat_id)
        for r in observations
        if r.tool_id == "modelvet"
        and r.eligibility == "SUPPORTED_CONTEXT"
        and r.outcome != "UNAVAILABLE"
    }
    repeated = [
        rows
        for rows in grouped.values()
        if len(rows) > 1
        and all(r.eligibility == "SUPPORTED_CONTEXT" and r.outcome != "UNAVAILABLE" for r in rows)
    ]
    stable = sum(
        len({(r.outcome, r.decision, r.tool_version) for r in rows}) == 1 for rows in repeated
    )
    return {
        "scope": "SYNTHETIC_DEVELOPMENT_ONLY",
        "tools": tools,
        "joint_context_observations": len(pair_keys),
        "repeated_groups": len(repeated),
        "stable_repeated_groups": stable,
        "reviewed_discrepancy_denominator": 0,
        "false_clean_rate": None,
        "benign_malicious_false_positive_rate": None,
        "incremental_detection_rate": None,
        "confidence_interval": None,
        "unmeasured_reason": (
            "No independent adjudication, hidden holdout or reviewed discrepancy positives."
        ),
    }
