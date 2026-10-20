"""Bounded signature/suffix classification; recognition is not validation."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath

from modelvet.core.bytes import read_prefix
from modelvet.core.snapshot import Snapshot
from modelvet.inventory.identity import ArtifactFile

APPLICABILITY_VERSION = "2"


class FileFormat(StrEnum):
    SAFETENSORS = "SAFETENSORS"
    PICKLE_LIKE = "PICKLE_LIKE"
    PYTORCH_ZIP = "PYTORCH_ZIP"
    ZIP_OTHER = "ZIP_OTHER"
    JSON = "JSON"
    MARKDOWN = "MARKDOWN"
    TEXT = "TEXT"
    PYTHON_SOURCE = "PYTHON_SOURCE"
    BINARY_UNKNOWN = "BINARY_UNKNOWN"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class FileClassification:
    format_class: FileFormat
    check_ids: tuple[str, ...]
    mismatch: bool = False
    reason: str | None = None
    signature: str | None = None


def applicable_checks(format_class: FileFormat) -> tuple[str, ...]:
    additional = {
        FileFormat.SAFETENSORS: ("structural:safetensors",),
        FileFormat.PICKLE_LIKE: ("modelscan", "scanner:resources"),
        FileFormat.PYTORCH_ZIP: ("structural:zip", "modelscan", "scanner:resources"),
        FileFormat.ZIP_OTHER: ("structural:zip", "modelscan", "scanner:resources"),
        FileFormat.JSON: ("metadata:local",),
        FileFormat.MARKDOWN: ("metadata:local",),
        FileFormat.TEXT: ("metadata:local",),
        FileFormat.PYTHON_SOURCE: ("source:presence",),
    }.get(format_class, ())
    return ("identity", "classification", *additional)


class Classifier:
    def classify(self, file: ArtifactFile, snapshot: Snapshot) -> FileClassification:
        head = read_prefix(snapshot, file, min(512, snapshot.source.limits.max_metadata_bytes))
        path = PurePosixPath(file.relpath)
        suffix = path.suffix.lower()
        expected = {
            ".safetensors": FileFormat.SAFETENSORS,
            ".pt": FileFormat.PICKLE_LIKE,
            ".pth": FileFormat.PICKLE_LIKE,
            ".pkl": FileFormat.PICKLE_LIKE,
            ".pickle": FileFormat.PICKLE_LIKE,
            ".zip": FileFormat.ZIP_OTHER,
            ".json": FileFormat.JSON,
            ".md": FileFormat.MARKDOWN,
            ".txt": FileFormat.TEXT,
            ".py": FileFormat.PYTHON_SOURCE,
        }.get(suffix)
        if path.name.upper() in {"LICENSE", "NOTICE", "COPYING"}:
            expected = FileFormat.TEXT
        detected = None
        signature = None
        if head[:4] in {b"PK\x03\x04", b"PK\x05\x06"}:
            detected = FileFormat.PYTORCH_ZIP if suffix in {".pt", ".pth"} else FileFormat.ZIP_OTHER
            signature = "zip"
        elif len(head) >= 2 and head[0] == 0x80 and head[1] <= 5:
            detected, signature = FileFormat.PICKLE_LIKE, "pickle-protocol"
        elif (
            len(head) >= 9
            and head[8:9] == b"{"
            and 1
            <= int.from_bytes(head[:8], "little")
            <= min(file.size - 8, snapshot.source.limits.max_metadata_bytes)
        ):
            detected, signature = FileFormat.SAFETENSORS, "safetensors-header-candidate"
        mismatch = detected is not None and expected is not None and detected != expected
        if detected == FileFormat.PYTORCH_ZIP and expected == FileFormat.PICKLE_LIKE:
            mismatch = False
        kind: FileFormat
        if expected == FileFormat.PYTHON_SOURCE:
            kind = expected
        elif detected is not None:
            kind = detected
        elif expected is not None:
            kind = expected
            if kind in {FileFormat.SAFETENSORS, FileFormat.PICKLE_LIKE, FileFormat.ZIP_OTHER}:
                mismatch = True
        else:
            kind = FileFormat.BINARY_UNKNOWN if b"\0" in head else FileFormat.UNKNOWN
        reason = "Suffix/signature inconsistent or unconfirmed." if mismatch else None
        if kind in {FileFormat.UNKNOWN, FileFormat.BINARY_UNKNOWN}:
            reason = "Unsupported security-relevant format."
        checks = applicable_checks(kind)
        if file.relpath == "modelvet-environment.json":
            checks += ("dependencies:declared",)
        return FileClassification(kind, checks, mismatch, reason, signature)
