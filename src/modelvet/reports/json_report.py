"""Strict report v1, reference integrity and timestamp-independent semantics."""

import hashlib
import json
import os
import re
import stat
from dataclasses import asdict
from pathlib import Path
from typing import Annotated, Any, Literal, Self

from pydantic import Field, ValidationError, model_validator

from modelvet.core.errors import InvalidInput
from modelvet.core.json_data import strict_json
from modelvet.coverage.conflicts import check_reference
from modelvet.coverage.reconciler import CoverageReconciler, expectations_for
from modelvet.evidence.models import (
    SHA256,
    ArtifactDigest,
    CheckRecord,
    ConflictRecord,
    CoverageRecord,
    DependencyRecord,
    EvidenceBundle,
    Finding,
    MetadataClaim,
    ToolExecution,
    ToolInfo,
    WireModel,
)
from modelvet.inventory.classify import FileClassification, FileFormat, applicable_checks
from modelvet.inventory.discover import FileObservation, stat_identity
from modelvet.inventory.gate import absolute_path, open_directory
from modelvet.inventory.identity import ArtifactManifest, manifest_from_entries
from modelvet.policies.models import BUILTIN_RULE_IDS, AdmissionDecision, DecisionState, Policy
from modelvet.reports.privacy import SENSITIVE_FIELD_PATTERN, redact

MAX_REPORT_BYTES = 32 * 1024 * 1024


class ArtifactIdentity(WireModel):
    manifest_digest: ArtifactDigest
    hash_algorithm: Literal["sha256"] = "sha256"
    file_count: Annotated[int, Field(ge=0, le=10000)]
    total_bytes: Annotated[int, Field(ge=0, le=2 * 1024**3)]


class ReportFile(WireModel):
    file_id: SHA256
    relpath: str
    size: Annotated[int, Field(ge=0, le=1024**3)]
    sha256: SHA256
    format_class: FileFormat
    mismatch: bool = False


class RunMetadata(WireModel):
    run_id: Annotated[str, Field(pattern=r"^[a-f0-9]{32}$")]
    started_at: str
    finished_at: str
    modelvet_version: str
    host_os_family: Literal["Linux", "Darwin"]
    result_status: Literal["COMPLETE", "DEGRADED"]

    @model_validator(mode="after")
    def utc_times(self) -> Self:
        from datetime import datetime

        for value in (self.started_at, self.finished_at):
            ToolExecution.utc_timestamp(value)
        if datetime.fromisoformat(self.finished_at) < datetime.fromisoformat(self.started_at):
            raise ValueError("Run timestamps are reversed.")
        return self


class RawEvidence(WireModel):
    digest: SHA256
    size: Annotated[int, Field(ge=0, le=4 * 1024 * 1024)]
    filename: Annotated[str, Field(pattern=r"^raw/[a-f0-9]{64}\.bin$")]


def semantic_content(data: dict[str, Any]) -> dict[str, Any]:
    """Raw bytes include vendor timestamps, cwd and logs; they are observational."""
    data = json.loads(json.dumps(data))
    for key in ("run", "semantic_digest", "raw_evidence"):
        data.pop(key, None)
    for check in data["checks"]:
        check.pop("raw_ref", None)
    for execution in data["executions"]:
        for key in (
            "started_at",
            "ended_at",
            "stdout_digest",
            "stderr_digest",
            "raw_report_digest",
            "environment_digest",
        ):
            execution.pop(key, None)
    for finding in data["findings"]:
        ref = finding["source_ref"]
        if ref.startswith("sha256:") and "#" in ref:
            finding["source_ref"] = "raw:modelscan#" + ref.split("#", 1)[1]
    data["references"] = {k: v for k, v in data["references"].items() if not k.startswith("raw:")}
    for field in ("prohibitions", "controls", "control_rules"):
        data["policy"][field] = sorted(
            data["policy"][field], key=lambda row: json.dumps(row, sort_keys=True)
        )
    return data


def semantic_digest(data: dict[str, Any]) -> str:
    encoded = json.dumps(
        semantic_content(data), sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return "sha256:" + hashlib.sha256(b"modelvet-report-v1\0" + encoded.encode()).hexdigest()


class Report(WireModel):
    schema_version: Literal["1.0.0"]
    artifact: ArtifactIdentity
    manifest_digest: ArtifactDigest
    run: RunMetadata
    policy: Policy
    policy_digest: ArtifactDigest
    tools: tuple[ToolInfo, ...]
    files: tuple[ReportFile, ...]
    checks: tuple[CheckRecord, ...]
    executions: tuple[ToolExecution, ...]
    findings: tuple[Finding, ...]
    coverage: tuple[CoverageRecord, ...]
    claims: tuple[MetadataClaim, ...]
    dependencies: tuple[DependencyRecord, ...]
    conflicts: tuple[ConflictRecord, ...]
    decision: AdmissionDecision
    limitations: tuple[str, ...]
    raw_evidence: tuple[RawEvidence, ...]
    references: dict[str, str]
    semantic_digest: ArtifactDigest

    @model_validator(mode="after")
    def integrity(self) -> Self:
        manifest = manifest_from_entries(
            tuple(FileObservation(f.relpath, f.size, f.sha256) for f in self.files)
        )
        if (
            manifest.manifest_digest != self.manifest_digest
            or self.artifact.manifest_digest != self.manifest_digest
            or tuple(f.file_id for f in manifest.files) != tuple(f.file_id for f in self.files)
            or self.artifact.file_count != len(self.files)
            or self.artifact.total_bytes != manifest.total_bytes
            or self.policy.semantic_digest != self.policy_digest
        ):
            raise ValueError("Report artifact/policy identity mismatch.")
        ids = {f.file_id for f in self.files}
        if any(
            c.file_id not in ids or c.artifact_digest != self.manifest_digest for c in self.checks
        ):
            raise ValueError("Unbound check identity.")
        classes = {
            f.file_id: FileClassification(
                f.format_class, applicable_checks(f.format_class), f.mismatch
            )
            for f in self.files
        }
        actual = CoverageReconciler().reconcile(
            manifest,
            expectations_for(manifest, classes, frozenset(self.policy.mandatory_checks)),
            list(self.checks),
        )
        if sorted(c.model_dump_json() for c in actual) != sorted(
            c.model_dump_json() for c in self.coverage
        ):
            raise ValueError("Report coverage differs from independent observations.")
        if self.decision.state in {DecisionState.APPROVE, DecisionState.CONTROLS} and (
            not self.files
            or any(row.mandatory_unresolved for row in self.coverage)
            or any(c.decision_relevant for c in self.conflicts)
            or self.findings
        ):
            raise ValueError("Admission contradicts incomplete evidence.")
        rules = (
            BUILTIN_RULE_IDS
            | {r.rule_id for r in self.policy.prohibitions}
            | {r.rule_id for r in self.policy.control_rules}
        )
        if not set(self.decision.rule_ids) <= rules:
            raise ValueError("Decision references an unknown policy rule.")
        check_pairs = {(c.file_id, c.check_id) for c in self.checks}
        tool_ids = {tool.tool_id for tool in self.tools}
        if (
            len(tool_ids) != len(self.tools)
            or any(
                check.status == "COMPLETE" and check.executor_id not in tool_ids
                for check in self.checks
            )
            or any(e.status != "NOT_RUN" and e.tool_id not in tool_ids for e in self.executions)
        ):
            raise ValueError("Complete evidence lacks a unique versioned producer.")
        if any((f.file_id, f.check_id) not in check_pairs for f in self.findings):
            raise ValueError("Finding has no corresponding assessment.")
        source_hashes = {f.file_id: f.sha256 for f in self.files}
        if any(
            c.source_file_id not in ids or c.source_sha256 != source_hashes[c.source_file_id]
            for c in self.claims
        ):
            raise ValueError("Unbound metadata claim.")
        raw_ids = {r.digest for r in self.raw_evidence}
        if len(raw_ids) != len(self.raw_evidence):
            raise ValueError("Duplicate raw evidence identity.")
        if any(
            f.source_ref.startswith("sha256:") and f.source_ref.split("#", 1)[0][7:] not in raw_ids
            for f in self.findings
        ):
            raise ValueError("Finding references missing raw evidence.")
        for record in self.raw_evidence:
            if record.filename != f"raw/{record.digest}.bin":
                raise ValueError("Raw evidence filename differs from identity.")
        for check in self.checks:
            if check.raw_ref and check.raw_ref.removeprefix("sha256:") not in raw_ids:
                raise ValueError("Missing raw check evidence.")
        for execution in self.executions:
            if execution.artifact_digest != self.manifest_digest or any(
                digest and digest not in raw_ids
                for digest in (
                    execution.stdout_digest,
                    execution.stderr_digest,
                    execution.raw_report_digest,
                )
            ):
                raise ValueError("Missing raw execution evidence or artifact mismatch.")
        content = self.model_dump(mode="json")
        for reference, pointer in self.references.items():
            value: Any = content
            try:
                for component in pointer.removeprefix("/").split("/"):
                    value = value[int(component)] if isinstance(value, list) else value[component]
            except (KeyError, IndexError, ValueError, TypeError) as exc:
                raise ValueError("Dangling reference index.") from exc
            if not reference or not pointer.startswith("/"):
                raise ValueError("Invalid reference index.")
        refs = list(self.decision.evidence_refs)
        refs += [r for c in self.conflicts for r in c.check_refs]
        refs += ["claim:" + r for c in self.conflicts for r in c.claim_ids]
        if not set(refs) <= self.references.keys():
            raise ValueError("Dangling decision/conflict evidence reference.")
        if self.semantic_digest != semantic_digest(content):
            raise ValueError("Semantic report digest mismatch.")
        return self


class ReportBuilder:
    def build(
        self,
        manifest: ArtifactManifest,
        evidence: EvidenceBundle,
        policy: Policy,
        decision: AdmissionDecision,
        run: RunMetadata,
        *,
        classifications: dict[str, FileClassification],
        coverage: list[CoverageRecord],
        conflicts: list[ConflictRecord],
        raw_payloads: dict[str, bytes] | None = None,
        private_roots: tuple[str, ...] = (),
    ) -> Report:
        payloads = raw_payloads or {}
        if any(hashlib.sha256(value).hexdigest() != key for key, value in payloads.items()):
            raise InvalidInput("Raw payload identity mismatch.")
        checks = sorted(evidence.checks, key=lambda c: (c.file_id, c.check_id, check_reference(c)))
        claims = sorted(evidence.claims, key=lambda c: c.claim_id)
        findings = sorted(evidence.findings, key=lambda f: f.finding_id)
        conflicts = sorted(conflicts, key=lambda c: c.conflict_id)
        coverage = sorted(coverage, key=lambda c: c.file_id)
        references = {manifest.manifest_digest: "/artifact"}
        references.update(
            {"file:" + f.file_id: f"/files/{i}" for i, f in enumerate(manifest.files)}
        )
        references.update({check_reference(c): f"/checks/{i}" for i, c in enumerate(checks)})
        for collection, prefix, items, attr in (
            ("claims", "claim:", claims, "claim_id"),
            ("findings", "finding:", findings, "finding_id"),
            ("conflicts", "conflict:", conflicts, "conflict_id"),
        ):
            references.update(
                {prefix + getattr(item, attr): f"/{collection}/{i}" for i, item in enumerate(items)}
            )
        for i, row in enumerate(coverage):
            references.update(
                {
                    f"coverage:{row.file_id}:{check}": f"/coverage/{i}"
                    for check in row.expected_check_ids
                }
            )
        references.update(
            {
                "claim-kind:" + kind: f"/policy/required_claims/{i}"
                for i, kind in enumerate(policy.required_claims)
            }
        )
        raw_records = [
            RawEvidence(digest=key, size=len(value), filename=f"raw/{key}.bin")
            for key, value in sorted(payloads.items())
        ]
        references.update(
            {"raw:" + r.digest: f"/raw_evidence/{i}" for i, r in enumerate(raw_records)}
        )
        data = dict(
            schema_version="1.0.0",
            artifact=ArtifactIdentity(
                manifest_digest=manifest.manifest_digest,
                file_count=len(manifest.files),
                total_bytes=manifest.total_bytes,
            ).model_dump(mode="json"),
            manifest_digest=manifest.manifest_digest,
            run=run.model_dump(mode="json"),
            policy=policy.model_dump(mode="json"),
            policy_digest=policy.semantic_digest,
            tools=[
                t.model_dump(mode="json") for t in sorted(evidence.tools, key=lambda t: t.tool_id)
            ],
            files=[
                {
                    **asdict(f),
                    "format_class": classifications[f.file_id].format_class.value,
                    "mismatch": classifications[f.file_id].mismatch,
                }
                for f in manifest.files
            ],
            checks=[c.model_dump(mode="json") for c in checks],
            executions=[
                e.model_dump(mode="json")
                for e in sorted(evidence.executions, key=lambda e: e.execution_id)
            ],
            findings=[f.model_dump(mode="json") for f in findings],
            coverage=[c.model_dump(mode="json") for c in coverage],
            claims=[c.model_dump(mode="json") for c in claims],
            dependencies=[
                d.model_dump(mode="json")
                for d in sorted(evidence.dependencies, key=lambda d: (d.name, d.source_ref))
            ],
            conflicts=[c.model_dump(mode="json") for c in conflicts],
            decision=decision.model_dump(mode="json"),
            limitations=sorted(
                set(evidence.limitations)
                | {
                    "Static assessment only; no model loading, legal clearance "
                    "or universal safety guarantee.",
                    "Host paths and common credential patterns are redacted; "
                    "exact artifact filenames and private raw evidence may remain sensitive.",
                }
            ),
            raw_evidence=[r.model_dump(mode="json") for r in raw_records],
            references=references,
        )

        def sanitize(value: Any, key: str = "") -> Any:
            if re.fullmatch(SENSITIVE_FIELD_PATTERN, key, flags=re.IGNORECASE):
                return "<redacted>"
            if isinstance(value, str):
                # Identity/policy/reference fields are immutable audit inputs.
                return (
                    value
                    if key in {"relpath", "owner", "filename"}
                    else redact(value, private_roots)
                )
            if isinstance(value, list):
                return [sanitize(v, key) for v in value]
            if isinstance(value, dict):
                return {k: sanitize(v, k) for k, v in value.items()}
            return value

        # Policy bytes bind the effective rules and owner, so preserve that object.
        for field in (
            "checks",
            "executions",
            "findings",
            "claims",
            "dependencies",
            "conflicts",
            "limitations",
        ):
            data[field] = sanitize(data[field])
        data["semantic_digest"] = semantic_digest(data)
        return parse_report(json.dumps(data, sort_keys=True, allow_nan=False).encode())


def parse_report(raw: bytes) -> Report:
    try:
        strict_json(raw, MAX_REPORT_BYTES, max_tokens=2_000_000)
        return Report.model_validate_json(raw)
    except (ValidationError, ValueError, KeyError) as exc:
        raise InvalidInput(
            "Invalid report schema, identity, references or semantic digest."
        ) from exc


def serialize_report(report: Report) -> bytes:
    raw = (
        json.dumps(
            report.model_dump(mode="json"), sort_keys=True, indent=2, allow_nan=False
        ).encode()
        + b"\n"
    )
    parse_report(raw)
    return raw


def read_report(path: Path) -> Report:
    selected = absolute_path(path)
    try:
        parent = open_directory(selected.parent)
        try:
            fd = os.open(selected.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        finally:
            os.close(parent)
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_nlink != 1
                or before.st_size > MAX_REPORT_BYTES
            ):
                raise InvalidInput("Unsafe or oversized report file.")
            raw = stream.read(MAX_REPORT_BYTES + 1)
            if stat_identity(before) != stat_identity(os.fstat(stream.fileno())):
                raise InvalidInput("Report changed while reading.")
        return parse_report(raw)
    except OSError as exc:
        raise InvalidInput("Cannot safely read report file.") from exc
