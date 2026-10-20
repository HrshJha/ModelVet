"""Closed policy vocabulary and attributable four-state decisions."""

import hashlib
import json
from enum import StrEnum
from typing import Annotated, Literal, Self, get_args

from pydantic import Field, field_validator, model_validator

from modelvet.evidence.models import Identifier, WireModel

CheckID = Literal[
    "identity",
    "classification",
    "structural:safetensors",
    "structural:zip",
    "metadata:local",
    "dependencies:declared",
    "source:presence",
    "modelscan",
    "scanner:resources",
]
CHECK_IDS: frozenset[str] = frozenset(get_args(CheckID))
BASELINE_CHECKS = frozenset({"identity", "classification"})
RuleID = Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9_-]{0,63}$")]
BUILTIN_RULE_IDS = frozenset(
    {
        "INVALID-EVIDENCE",
        "MISSING-MANDATORY",
        "UNSUPPORTED-FORMAT",
        "NO-MODEL",
        "UNRESOLVED-CONFLICT",
        "MISSING-CLAIM",
        "UNRESOLVED-FINDING",
        "POLICY-APPROVE",
    }
)
Condition = Literal["REPOSITORY_CODE", "SERIALIZED_MODEL", "MODEL_PRESENT"]
ControlID = Literal["ISOLATED_LOADING", "NO_CODE_IMPORT"]
ClaimKind = Literal["LICENSE", "PROVENANCE", "DEPENDENCY"]


class Prohibition(WireModel):
    rule_id: RuleID
    category: Literal["REPOSITORY_CODE"]


class Control(WireModel):
    control_id: ControlID
    owner: Annotated[str, Field(min_length=1, max_length=256)]

    @field_validator("owner")
    @classmethod
    def printable_owner(cls, value: str) -> str:
        value.encode("utf-8", errors="strict")
        if (
            value != value.strip()
            or not value.strip()
            or any(ord(c) < 32 or ord(c) == 127 for c in value)
        ):
            raise ValueError("Control owner must be a nonempty printable name.")
        return value


class ControlRule(WireModel):
    rule_id: RuleID
    condition: Condition
    control_ids: Annotated[tuple[ControlID, ...], Field(min_length=1, max_length=2)]

    @field_validator("control_ids")
    @classmethod
    def unique_ids(cls, value: tuple[ControlID, ...]) -> tuple[ControlID, ...]:
        if len(set(value)) != len(value):
            raise ValueError("Duplicate control IDs.")
        return tuple(sorted(value))


class Policy(WireModel):
    schema_version: Literal["1.0.0"]
    policy_id: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")]
    policy_version: Annotated[str, Field(pattern=r"^[1-9][0-9]{0,8}$")]
    applicability_version: Literal["2"]
    mandatory_checks: tuple[CheckID, ...]
    optional_checks: tuple[CheckID, ...]
    prohibitions: Annotated[tuple[Prohibition, ...], Field(max_length=32)]
    controls: Annotated[tuple[Control, ...], Field(max_length=2)]
    control_rules: Annotated[tuple[ControlRule, ...], Field(max_length=32)]
    required_claims: tuple[ClaimKind, ...] = ()

    @field_validator("mandatory_checks", "optional_checks", "required_claims")
    @classmethod
    def sorted_unique(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("Duplicate policy entries.")
        return tuple(sorted(value))

    @model_validator(mode="after")
    def coherent_rules(self) -> Self:
        mandatory, optional = set(self.mandatory_checks), set(self.optional_checks)
        if mandatory & optional or mandatory | optional != CHECK_IDS:
            raise ValueError("Every known check must be mandatory or explicitly optional.")
        if not BASELINE_CHECKS <= mandatory:
            raise ValueError("Identity and classification cannot be optional.")
        rules = [r.rule_id for r in self.prohibitions] + [r.rule_id for r in self.control_rules]
        categories = [r.category for r in self.prohibitions]
        conditions = [r.condition for r in self.control_rules]
        control_ids = [control.control_id for control in self.controls]
        if (
            len(set(rules)) != len(rules)
            or set(rules) & BUILTIN_RULE_IDS
            or len(set(categories)) != len(categories)
            or len(set(conditions)) != len(conditions)
            or len(set(control_ids)) != len(control_ids)
        ):
            raise ValueError("Duplicate or reserved policy rule/control.")
        if set(categories) & set(conditions):
            raise ValueError("One condition cannot be both prohibited and controlled.")
        referenced = {control for rule in self.control_rules for control in rule.control_ids}
        if referenced != set(control_ids):
            raise ValueError("Control references must exactly match declared controls.")
        return self

    @property
    def semantic_digest(self) -> str:
        content = self.model_dump(mode="json")
        for field in ("prohibitions", "controls", "control_rules"):
            content[field] = sorted(content[field], key=lambda row: json.dumps(row, sort_keys=True))
        encoded = json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return "sha256:" + hashlib.sha256(b"modelvet-policy-v1\0" + encoded.encode()).hexdigest()


class DecisionState(StrEnum):
    APPROVE = "APPROVE"
    CONTROLS = "CONTROLS"
    BLOCK = "BLOCK"
    INSUFFICIENT = "INSUFFICIENT"


class AdmissionDecision(WireModel):
    state: DecisionState
    rule_ids: Annotated[tuple[RuleID, ...], Field(min_length=1)]
    reason: Annotated[str, Field(min_length=1, max_length=4096)]
    evidence_refs: tuple[Identifier, ...]
    required_controls: tuple[Control, ...] = ()

    @model_validator(mode="after")
    def attributable_controls(self) -> Self:
        if (self.state == DecisionState.CONTROLS) != bool(self.required_controls):
            raise ValueError("Only CONTROLS decisions must name controls and owners.")
        if self.state == DecisionState.BLOCK and not self.evidence_refs:
            raise ValueError("BLOCK needs independent evidence references.")
        return self
