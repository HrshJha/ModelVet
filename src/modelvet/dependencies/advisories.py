"""Offline matching of explicit PyPI versions in operator-supplied OSV snapshots.

This is supplementary evidence. It never changes a stored admission decision.
Unsupported ranges and missing/partial queries cannot prove no affected version.
"""

import hashlib
import json
import os
import re
import stat
from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import ConfigDict, Field, JsonValue, ValidationError, field_validator, model_validator

from modelvet.core.errors import InvalidInput
from modelvet.core.json_data import strict_json
from modelvet.dependencies.manifest import _PIN, DependencyDeclaration
from modelvet.evidence.models import SHA256, ArtifactDigest, DependencyRecord, WireModel
from modelvet.inventory.discover import stat_identity
from modelvet.inventory.gate import absolute_path, open_directory

MAX_SNAPSHOT_BYTES = 16 * 1024 * 1024
Text = Annotated[str, Field(min_length=1, max_length=256)]
Version = Annotated[str, Field(min_length=1, max_length=100)]


def utc_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
        if "T" not in value or not value.endswith(("Z", "+00:00")):
            raise ValueError
        if parsed.utcoffset() != timedelta(0):
            raise ValueError
        return parsed
    except (TypeError, ValueError) as exc:
        raise InvalidInput("Advisory timestamps must be UTC RFC3339.") from exc


def package_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


class Package(WireModel):
    name: Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,199}$")]
    ecosystem: Text


class OSVPackage(Package):
    # OSV minor versions may add fields, including purl; never execute them.
    model_config = ConfigDict(extra="ignore", strict=True, frozen=True)


class Affected(WireModel):
    model_config = ConfigDict(extra="ignore", strict=True, frozen=True)
    package: OSVPackage
    versions: Annotated[tuple[Version, ...], Field(max_length=10000)] = ()
    ranges: Annotated[tuple[JsonValue, ...], Field(max_length=1000)] = ()
    ecosystem_specific: dict[str, JsonValue] = Field(default_factory=dict)


class OSVRecord(WireModel):
    model_config = ConfigDict(extra="ignore", strict=True, frozen=True)
    schema_version: Annotated[str, Field(pattern=r"^\d+\.\d+\.\d+$")] = "1.0.0"
    id: Annotated[str, Field(pattern=r"^[a-zA-Z0-9:_.-]{1,256}$")]
    modified: Text
    withdrawn: Text | None = None
    affected: Annotated[tuple[Affected, ...], Field(max_length=1000)] = ()

    @field_validator("modified", "withdrawn")
    @classmethod
    def timestamp(cls, value: str | None) -> str | None:
        if value is not None:
            utc_time(value)
        return value


class QueryResponse(WireModel):
    vulns: Annotated[tuple[OSVRecord, ...], Field(max_length=1000)] = ()
    next_page_token: Annotated[str, Field(max_length=4096)] | None = None


class SnapshotQuery(WireModel):
    package: Package
    version: Version
    complete: bool
    response: QueryResponse


class AdvisorySnapshot(WireModel):
    schema_version: Literal["1.0.0"]
    generated_at: Text
    source: Annotated[str, Field(min_length=1, max_length=2048)]
    queries: Annotated[tuple[SnapshotQuery, ...], Field(max_length=1000)]

    @field_validator("generated_at")
    @classmethod
    def timestamp(cls, value: str) -> str:
        utc_time(value)
        return value


class AdvisoryMatch(WireModel):
    advisory_id: Text
    source_ref: str


class DependencyAdvisories(WireModel):
    name: Text
    ecosystem: Text
    version: str | None
    dependency_source_ref: str
    status: Literal["COMPLETE", "INCONCLUSIVE", "UNSUPPORTED", "NOT_RUN"]
    result: Literal["AFFECTED_VERSION", "NO_MATCH_IN_SNAPSHOT", "UNKNOWN"]
    matches: Annotated[tuple[AdvisoryMatch, ...], Field(max_length=1000)] = ()
    reasons: tuple[str, ...] = ()

    @model_validator(mode="after")
    def consistent(self) -> Self:
        if bool(self.matches) != (self.result == "AFFECTED_VERSION"):
            raise ValueError("Affected-version result must have matching source records.")
        if self.result == "NO_MATCH_IN_SNAPSHOT" and self.status != "COMPLETE":
            raise ValueError("Unresolved evidence cannot establish a no-match result.")
        if self.status == "COMPLETE" and (self.result == "UNKNOWN" or self.reasons):
            raise ValueError("Complete evidence cannot contain unresolved predicates.")
        return self


class AdvisoryAssessment(WireModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    artifact_digest: ArtifactDigest
    report_digest: ArtifactDigest
    snapshot_digest: ArtifactDigest | None
    snapshot_generated_at: str | None
    source_claim_sha256: SHA256 | None
    evaluated_at: str
    max_age_days: Annotated[int, Field(ge=0, le=365)]
    required: bool
    status: Literal["COMPLETE", "INCONCLUSIVE", "NOT_RUN"]
    dependencies: Annotated[tuple[DependencyAdvisories, ...], Field(max_length=1000)]
    admission_recomputed: Literal[False] = False
    limitations: tuple[str, ...] = (
        "Operator-supplied snapshot and completeness declarations are not authenticated.",
        "Exact PyPI version strings only; ranges and other ecosystems remain unresolved.",
        "No match applies only to supplied query evidence, not to all vulnerabilities.",
        "Declared dependency pins do not establish installation, reachability or exploitability.",
        "Supplementary evidence does not replace or promote the stored admission decision.",
    )

    @model_validator(mode="after")
    def consistent(self) -> Self:
        now = utc_time(self.evaluated_at)
        present = self.snapshot_digest is not None
        if present != (self.snapshot_generated_at is not None):
            raise ValueError("Snapshot identity and generation time must appear together.")
        if present != (self.source_claim_sha256 is not None):
            raise ValueError("Snapshot source claim identity is required.")
        expected = (
            "NOT_RUN"
            if not present
            else (
                "COMPLETE"
                if self.dependencies and all(d.status == "COMPLETE" for d in self.dependencies)
                else "INCONCLUSIVE"
            )
        )
        if self.status != expected:
            raise ValueError("Aggregate status must reflect every dependency.")
        if not present and any(d.status != "NOT_RUN" for d in self.dependencies):
            raise ValueError("Missing snapshot cannot yield assessed evidence.")
        if self.snapshot_generated_at is not None:
            age = now - utc_time(self.snapshot_generated_at)
            if not timedelta(0) <= age <= timedelta(days=self.max_age_days):
                if any(d.status == "COMPLETE" for d in self.dependencies):
                    raise ValueError("Unresolved freshness cannot complete evidence.")
        for dependency in self.dependencies:
            for match in dependency.matches:
                if not match.source_ref.startswith(f"{self.snapshot_digest}#/queries/"):
                    raise ValueError("Advisory source must bind the snapshot digest.")
        return self

    @property
    def exit_code(self) -> int:
        if any(row.matches for row in self.dependencies):
            return 30
        return 30 if self.required and self.status != "COMPLETE" else 0

    @property
    def semantic_digest(self) -> str:
        encoded = json.dumps(self.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        return (
            "sha256:" + hashlib.sha256(b"modelvet-advisories-v1\0" + encoded.encode()).hexdigest()
        )


class AdvisoryDocument(WireModel):
    assessment: AdvisoryAssessment
    semantic_digest: ArtifactDigest
    exit_code: Literal[0, 30]

    @model_validator(mode="after")
    def consistent(self) -> Self:
        if self.semantic_digest != self.assessment.semantic_digest:
            raise ValueError("Advisory semantic digest mismatch.")
        if self.exit_code != self.assessment.exit_code:
            raise ValueError("Advisory exit classification mismatch.")
        return self

    @classmethod
    def from_assessment(cls, assessment: AdvisoryAssessment) -> Self:
        return cls.model_validate(
            {
                "assessment": assessment,
                "semantic_digest": assessment.semantic_digest,
                "exit_code": assessment.exit_code,
            }
        )


def load_snapshot(path: Path) -> tuple[AdvisorySnapshot, str]:
    """Read a single bounded regular file, refusing links and identity drift."""
    selected = absolute_path(path)
    try:
        parent = open_directory(selected.parent)
        try:
            fd = os.open(
                selected.name,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                dir_fd=parent,
            )
            with os.fdopen(fd, "rb") as stream:
                before = os.fstat(stream.fileno())
                if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                    raise InvalidInput("Advisory snapshot must be regular and have one link.")
                if before.st_size > MAX_SNAPSHOT_BYTES:
                    raise InvalidInput("Advisory snapshot exceeds 16 MiB.")
                raw = stream.read(MAX_SNAPSHOT_BYTES + 1)
                after = os.fstat(stream.fileno())
                if stat_identity(before) != stat_identity(after) or len(raw) != before.st_size:
                    raise InvalidInput("Advisory snapshot changed while reading.")
        finally:
            os.close(parent)
    except OSError as exc:
        raise InvalidInput("Cannot safely read the advisory snapshot.") from exc
    data = strict_json(raw, MAX_SNAPSHOT_BYTES)
    try:
        snapshot = AdvisorySnapshot.model_validate_json(json.dumps(data, allow_nan=False))
    except (ValueError, ValidationError) as exc:
        raise InvalidInput("Invalid advisory snapshot envelope or OSV record.") from exc
    generated = utc_time(snapshot.generated_at)
    keys = set()
    record_identities: dict[str, str] = {}
    count = 0
    for query in snapshot.queries:
        key = (query.package.ecosystem, package_name(query.package.name), query.version)
        if key in keys:
            raise InvalidInput("Duplicate advisory query identity.")
        keys.add(key)
        ids = set()
        for record in query.response.vulns:
            count += 1
            if count > 1000 or record.id in ids:
                raise InvalidInput("Duplicate or excessive advisory records.")
            ids.add(record.id)
            identity = json.dumps(record.model_dump(mode="json"), sort_keys=True)
            if record.id in record_identities and record_identities[record.id] != identity:
                raise InvalidInput("Conflicting advisory records share one ID.")
            record_identities[record.id] = identity
            if utc_time(record.modified) > generated or (
                record.withdrawn is not None and utc_time(record.withdrawn) > generated
            ):
                raise InvalidInput("Advisory record postdates snapshot generation.")
    return snapshot, "sha256:" + hashlib.sha256(raw).hexdigest()


class AdvisoryReader:
    def assess(
        self,
        dependencies: tuple[DependencyRecord | DependencyDeclaration, ...],
        *,
        snapshot_path: Path | None,
        as_of: str,
        artifact_digest: str,
        report_digest: str,
        max_age_days: int = 7,
        required: bool = True,
    ) -> AdvisoryAssessment:
        now = utc_time(as_of)
        if type(max_age_days) is not int or not 0 <= max_age_days <= 365:
            raise InvalidInput("Advisory maximum age must be 0–365 days.")
        if len(dependencies) > 1000:
            raise InvalidInput("Too many dependencies for advisory matching.")
        snapshot, digest = load_snapshot(snapshot_path) if snapshot_path else (None, None)
        time_reason = None
        if snapshot:
            age = now - utc_time(snapshot.generated_at)
            if age < timedelta(0):
                time_reason = "Snapshot is future-dated relative to evaluation."
            elif age > timedelta(days=max_age_days):
                time_reason = "Snapshot is stale relative to evaluation."
        queries = {
            (q.package.ecosystem, package_name(q.package.name), q.version): (index, q)
            for index, q in enumerate(snapshot.queries if snapshot else ())
        }
        names = [(d.ecosystem, package_name(d.name)) for d in dependencies]
        rows = []
        for dependency in dependencies:
            name = package_name(dependency.name)
            reasons = []
            matches = []
            status: Literal["COMPLETE", "INCONCLUSIVE", "UNSUPPORTED", "NOT_RUN"] = "COMPLETE"
            if snapshot is None:
                status = "NOT_RUN"
                reasons.append("No advisory snapshot supplied.")
            elif (
                dependency.ecosystem != "PyPI"
                or dependency.status != "DECLARED_PINNED"
                or dependency.version is None
                or not _PIN.fullmatch(dependency.version)
            ):
                status = "UNSUPPORTED"
                reasons.append("Dependency ecosystem or exact pin is unresolved.")
            elif names.count((dependency.ecosystem, name)) != 1:
                status = "INCONCLUSIVE"
                reasons.append("Duplicate or conflicting dependency declarations.")
            else:
                query_pair = queries.get((dependency.ecosystem, name, dependency.version))
                if query_pair is None:
                    reasons.append("No query evidence for this exact package/version.")
                else:
                    index, query = query_pair
                    if not query.complete or query.response.next_page_token:
                        reasons.append("Snapshot query is partial or paginated.")
                    for number, record in enumerate(query.response.vulns):
                        if not record.schema_version.startswith("1."):
                            reasons.append("Unsupported OSV schema major version.")
                            continue
                        if record.withdrawn is not None:
                            continue
                        relevant = [
                            a
                            for a in record.affected
                            if a.package.ecosystem == "PyPI"
                            and package_name(a.package.name) == name
                        ]
                        if not relevant:
                            reasons.append("Query record has no matching affected package.")
                        matched = any(dependency.version in a.versions for a in relevant)
                        if matched:
                            matches.append(
                                AdvisoryMatch(
                                    advisory_id=record.id,
                                    source_ref=f"{digest}#/queries/{index}/response/vulns/{number}",
                                )
                            )
                        if any(
                            a.ranges or a.ecosystem_specific or not a.versions for a in relevant
                        ):
                            reasons.append("Affected range or ecosystem semantics are unsupported.")
                if time_reason:
                    reasons.append(time_reason)
                if reasons:
                    status = "INCONCLUSIVE"
            rows.append(
                DependencyAdvisories(
                    name=name,
                    ecosystem=dependency.ecosystem,
                    version=dependency.version,
                    dependency_source_ref=dependency.source_ref,
                    status=status,
                    result="AFFECTED_VERSION"
                    if matches
                    else ("NO_MATCH_IN_SNAPSHOT" if status == "COMPLETE" else "UNKNOWN"),
                    matches=tuple(sorted(matches, key=lambda m: m.advisory_id)),
                    reasons=tuple(sorted(set(reasons))),
                )
            )
        overall: Literal["COMPLETE", "INCONCLUSIVE", "NOT_RUN"] = (
            "NOT_RUN"
            if snapshot is None
            else (
                "COMPLETE" if rows and all(r.status == "COMPLETE" for r in rows) else "INCONCLUSIVE"
            )
        )
        return AdvisoryAssessment(
            artifact_digest=artifact_digest,
            report_digest=report_digest,
            snapshot_digest=digest,
            snapshot_generated_at=snapshot.generated_at if snapshot else None,
            source_claim_sha256=hashlib.sha256(snapshot.source.encode()).hexdigest()
            if snapshot
            else None,
            evaluated_at=now.isoformat(),
            max_age_days=max_age_days,
            required=required,
            status=overall,
            dependencies=tuple(
                sorted(
                    rows,
                    key=lambda r: (r.ecosystem, r.name, r.version or "", r.dependency_source_ref),
                )
            ),
        )
