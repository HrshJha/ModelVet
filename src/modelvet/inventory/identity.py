"""manifest-v1 canonical artifact identity and best-effort mutation detection."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from modelvet.core.errors import InvalidInput, SnapshotChanged
from modelvet.core.snapshot import Snapshot
from modelvet.inventory.discover import FileObservation, observe_directory, validate_relpath
from modelvet.inventory.gate import ValidatedInput, open_directory

if TYPE_CHECKING:
    from modelvet.evidence.models import CheckRecord


@dataclass(frozen=True)
class ArtifactFile:
    file_id: str
    relpath: str
    size: int
    sha256: str


@dataclass(frozen=True)
class ArtifactManifest:
    manifest_digest: str
    files: tuple[ArtifactFile, ...]

    @property
    def total_bytes(self) -> int:
        return sum(file.size for file in self.files)


def manifest_from_entries(entries: tuple[FileObservation, ...]) -> ArtifactManifest:
    digest = hashlib.sha256(b"modelvet-manifest-v1\n")
    files: list[ArtifactFile] = []
    seen: set[str] = set()
    for item in sorted(entries, key=lambda file: file.relpath.encode("utf-8")):
        path = validate_relpath(item.relpath)
        if path.casefold() in seen or type(item.size) is not int or item.size < 0:
            raise InvalidInput("Duplicate canonical path or invalid file size.")
        seen.add(path.casefold())
        if len(item.sha256) != 64 or any(char not in "0123456789abcdef" for char in item.sha256):
            raise InvalidInput("Invalid content SHA-256.")
        raw_path = path.encode("utf-8")
        digest.update(
            raw_path + b"\0" + str(item.size).encode() + b"\0" + item.sha256.encode() + b"\n"
        )
        file_id = hashlib.sha256(
            b"modelvet-file-v1\0" + raw_path + b"\0" + bytes.fromhex(item.sha256)
        ).hexdigest()
        files.append(ArtifactFile(file_id, path, item.size, item.sha256))
    return ArtifactManifest("sha256:" + digest.hexdigest(), tuple(files))


class InventoryService:
    def collect(self, snapshot: Snapshot) -> ArtifactManifest:
        fd = open_directory(snapshot.root)
        try:
            root = os.fstat(fd)
        finally:
            os.close(fd)
        current = observe_directory(
            ValidatedInput(
                snapshot.root,
                snapshot.source.output_dir,
                snapshot.source.limits,
                root.st_dev,
                root.st_ino,
            )
        )
        if current != snapshot.files:
            raise SnapshotChanged("Snapshot content differs from ingested bytes.")
        return manifest_from_entries(current)

    def verify_unchanged(self, source: ValidatedInput, manifest: ArtifactManifest) -> bool:
        try:
            return manifest_from_entries(observe_directory(source)) == manifest
        except (InvalidInput, OSError):
            return False

    def verify_snapshot(self, snapshot: Snapshot, manifest: ArtifactManifest) -> bool:
        try:
            return self.collect(snapshot) == manifest
        except (InvalidInput, OSError):
            return False


def final_identity_checks(
    snapshot: Snapshot, manifest: ArtifactManifest, checks: list[CheckRecord]
) -> list[CheckRecord]:
    """Recheck both byte sets before final evaluation; invalidate all drifted proof.

    This remains best-effort detection, not an atomic filesystem transaction.
    """
    from modelvet.evidence.models import CheckResult, CheckStatus

    inventory = InventoryService()
    source_ok = inventory.verify_unchanged(snapshot.source, manifest)
    snapshot_ok = inventory.verify_snapshot(snapshot, manifest)
    if source_ok and snapshot_ok:
        return list(checks)
    return [
        check.model_copy(
            update={
                "status": CheckStatus.FAILED,
                "result": CheckResult.UNKNOWN,
                "error_code": "IDENTITY_DRIFT",
                "reason": "Source or snapshot changed after ingestion.",
                "details": {
                    **check.details,
                    "source_unchanged": source_ok,
                    "snapshot_unchanged": snapshot_ok,
                },
            }
        )
        if check.check_id == "identity"
        else check
        for check in checks
    ]
