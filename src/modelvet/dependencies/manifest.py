"""Read user-supplied modelvet-environment.json as bounded, unverified claims."""

import re
from dataclasses import dataclass, replace
from typing import Literal

from modelvet.core.bytes import read_prefix
from modelvet.core.errors import InvalidInput
from modelvet.core.json_data import strict_json
from modelvet.core.snapshot import Snapshot
from modelvet.inventory.identity import ArtifactManifest, InventoryService
from modelvet.structural.base import Inspection

MANIFEST_NAME = "modelvet-environment.json"
_NAME = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,198}[A-Za-z0-9])?")
_PIN = re.compile(
    r"(?:[0-9]+!)?[0-9]+(?:\.[0-9]+)*(?:(?:a|b|rc)[0-9]+)?"
    r"(?:\.post[0-9]+)?(?:\.dev[0-9]+)?(?:\+[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*)?"
)


@dataclass(frozen=True)
class DependencyDeclaration:
    name: str
    ecosystem: str
    version: str | None
    source_ref: str
    source_sha256: str
    status: Literal["DECLARED_PINNED", "INCONCLUSIVE"]
    reason: str | None = None


@dataclass(frozen=True)
class DependencyAssessment:
    records: tuple[DependencyDeclaration, ...]
    check: Inspection
    file_id: str | None


class DependencyReader:
    def assess(
        self, snapshot: Snapshot, manifest: ArtifactManifest | None = None
    ) -> DependencyAssessment:
        manifest = manifest or InventoryService().collect(snapshot)
        file = next((file for file in manifest.files if file.relpath == MANIFEST_NAME), None)
        limitation = (
            "User-declared pins; actual installation, vulnerabilities and reachability unverified.",
        )
        if file is None:
            return DependencyAssessment(
                (),
                Inspection(
                    "dependencies:declared",
                    "UNSUPPORTED",
                    "No explicit environment manifest supplied.",
                    limitations=limitation,
                ),
                None,
            )
        records: list[DependencyDeclaration] = []
        try:
            if file.size > snapshot.source.limits.max_metadata_bytes:
                raise InvalidInput("Environment manifest exceeds metadata budget.")
            data = strict_json(
                read_prefix(snapshot, file, file.size), snapshot.source.limits.max_metadata_bytes
            )
            if not isinstance(data, dict) or set(data) != {"schema_version", "dependencies"}:
                raise InvalidInput("Invalid environment envelope.")
            if data["schema_version"] != "1.0.0":
                return DependencyAssessment(
                    (),
                    Inspection(
                        "dependencies:declared",
                        "UNSUPPORTED",
                        "Unsupported environment schema.",
                        limitations=limitation,
                    ),
                    file.file_id,
                )
            rows = data["dependencies"]
            if not isinstance(rows, list) or len(rows) > 1000:
                raise InvalidInput("Invalid or oversized dependency list.")
            seen: set[str] = set()
            duplicates: set[str] = set()
            for index, row in enumerate(rows):
                if (
                    not isinstance(row, dict)
                    or set(row) - {"name", "ecosystem", "version"}
                    or not isinstance(row.get("name"), str)
                    or not _NAME.fullmatch(row["name"])
                    or not isinstance(row.get("ecosystem"), str)
                    or len(row["ecosystem"]) > 100
                ):
                    raise InvalidInput("Invalid dependency declaration.")
                name = re.sub(r"[-_.]+", "-", row["name"]).lower()
                version = row.get("version")
                version = version if isinstance(version, str) and len(version) <= 100 else None
                pinned = (
                    row["ecosystem"] == "PyPI" and version is not None and _PIN.fullmatch(version)
                )
                records.append(
                    DependencyDeclaration(
                        name,
                        row["ecosystem"],
                        version,
                        f"{file.file_id}#json:/dependencies/{index}",
                        file.sha256,
                        "DECLARED_PINNED" if pinned else "INCONCLUSIVE",
                        None if pinned else "Unsupported ecosystem, missing or non-exact version.",
                    )
                )
                key = f"{row['ecosystem']}:{name}"
                if key in seen:
                    duplicates.add(key)
                seen.add(key)
            if duplicates:
                records = [
                    replace(record, status="INCONCLUSIVE", reason="Duplicate/conflicting pins.")
                    if f"{record.ecosystem}:{record.name}" in duplicates
                    else record
                    for record in records
                ]
            incomplete = any(record.status == "INCONCLUSIVE" for record in records)
            check = Inspection(
                "dependencies:declared",
                "UNSUPPORTED" if incomplete else "COMPLETE",
                "Incomplete or ambiguous dependency declarations." if incomplete else None,
                limitations=limitation,
            )
        except InvalidInput:
            check = Inspection(
                "dependencies:declared",
                "FAILED",
                "Malformed environment manifest.",
                limitations=limitation,
            )
        return DependencyAssessment(tuple(records), check, file.file_id)

    def read_manifest(self, snapshot: Snapshot) -> list[DependencyDeclaration]:
        return list(self.assess(snapshot).records)
