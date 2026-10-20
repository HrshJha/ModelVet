"""Verify only declared stored raw bytes; never rescan artifacts or admit models."""

import hashlib
import os
import re
import stat
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from modelvet.core.errors import InvalidInput
from modelvet.evidence.models import SHA256, ArtifactDigest, WireModel
from modelvet.inventory.discover import stat_identity
from modelvet.inventory.gate import absolute_path, open_directory
from modelvet.reports.json_report import parse_report, read_report_bytes

MAX_ATTACHMENTS = 64
MAX_RAW_BYTES = 32 * 1024 * 1024
AttachmentStatus = Literal[
    "VERIFIED", "MISSING", "UNSAFE", "SIZE_MISMATCH", "HASH_MISMATCH", "CHANGED", "BUDGET_EXCEEDED"
]


class AttachmentAudit(WireModel):
    digest: SHA256
    size: Annotated[int, Field(ge=0, le=4 * 1024 * 1024)]
    status: AttachmentStatus
    bytes_read: Annotated[int, Field(ge=0, le=4 * 1024 * 1024)] = 0

    @model_validator(mode="after")
    def consistent(self) -> Self:
        if self.bytes_read > self.size or (
            self.status == "VERIFIED" and self.bytes_read != self.size
        ):
            raise ValueError("Attachment read accounting is inconsistent.")
        return self


class ReportAudit(WireModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    report_sha256: SHA256
    artifact_digest: ArtifactDigest
    semantic_digest: ArtifactDigest
    status: Literal["VERIFIED", "INCOMPLETE"]
    report_pin_matches: bool | None
    report_unchanged: bool
    declared_attachments: Annotated[int, Field(ge=0)]
    verified_attachments: Annotated[int, Field(ge=0)]
    unresolved_attachments: Annotated[int, Field(ge=0)]
    omitted_attachments: Annotated[int, Field(ge=0)]
    raw_bytes_read: Annotated[int, Field(ge=0, le=MAX_RAW_BYTES)]
    attachments: Annotated[tuple[AttachmentAudit, ...], Field(max_length=MAX_ATTACHMENTS)]
    admission_recomputed: Literal[False] = False
    notice: Literal[
        "Stored byte consistency only; not a signature, source rescan or admission decision."
    ] = "Stored byte consistency only; not a signature, source rescan or admission decision."

    @model_validator(mode="after")
    def consistent(self) -> Self:
        verified = sum(a.status == "VERIFIED" for a in self.attachments)
        complete = (
            self.report_unchanged
            and self.report_pin_matches is not False
            and verified == self.declared_attachments
        )
        if (
            len({a.digest for a in self.attachments}) != len(self.attachments)
            or self.verified_attachments != verified
            or self.unresolved_attachments != self.declared_attachments - verified
            or self.omitted_attachments != self.declared_attachments - len(self.attachments)
            or self.raw_bytes_read != sum(a.bytes_read for a in self.attachments)
            or (self.status == "VERIFIED") != complete
        ):
            raise ValueError("Audit accounting or completion status disagrees with evidence.")
        return self


def _attachment(raw_fd: int, digest: str, size: int) -> AttachmentAudit:
    try:
        descriptor = os.open(
            digest + ".bin",
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
            dir_fd=raw_fd,
        )
    except FileNotFoundError:
        return AttachmentAudit(digest=digest, size=size, status="MISSING")
    except OSError:
        return AttachmentAudit(digest=digest, size=size, status="UNSAFE")
    count = 0
    try:
        with os.fdopen(descriptor, "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                return AttachmentAudit(digest=digest, size=size, status="UNSAFE")
            if before.st_size != size:
                return AttachmentAudit(digest=digest, size=size, status="SIZE_MISMATCH")
            observed = hashlib.sha256()
            while count < size:
                chunk = stream.read(min(65536, size - count))
                if not chunk:
                    break
                count += len(chunk)
                observed.update(chunk)
            after = os.fstat(stream.fileno())
            status: AttachmentStatus = "VERIFIED"
            if stat_identity(before) != stat_identity(after) or count != size:
                status = "CHANGED"
            elif observed.hexdigest() != digest:
                status = "HASH_MISMATCH"
            return AttachmentAudit(digest=digest, size=size, status=status, bytes_read=count)
    except OSError:
        return AttachmentAudit(digest=digest, size=size, status="UNSAFE", bytes_read=count)


def _audit_captured(
    path: Path,
    raw: bytes,
    *,
    expected_report_sha256: str | None = None,
    max_raw_bytes: int = MAX_RAW_BYTES,
    max_attachments: int = MAX_ATTACHMENTS,
) -> ReportAudit:
    if (
        type(max_raw_bytes) is not int
        or not 0 <= max_raw_bytes <= MAX_RAW_BYTES
        or type(max_attachments) is not int
        or not 0 <= max_attachments <= MAX_ATTACHMENTS
    ):
        raise InvalidInput("Audit budgets must be integers within hard ceilings.")
    if expected_report_sha256 is not None and not re.fullmatch(
        r"[a-f0-9]{64}", expected_report_sha256
    ):
        raise InvalidInput("Expected report SHA-256 must be 64 lowercase hex characters.")
    report = parse_report(raw)
    digest = hashlib.sha256(raw).hexdigest()
    pin_matches = digest == expected_report_sha256 if expected_report_sha256 else None
    rows = []
    parent_fd = raw_fd = None
    raw_status: AttachmentStatus = "UNSAFE"
    try:
        if report.raw_evidence:
            try:
                parent_fd = open_directory(absolute_path(path).parent)
                raw_fd = os.open(
                    "raw", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd
                )
            except FileNotFoundError:
                raw_status = "MISSING"
            except OSError:
                raw_status = "UNSAFE"
        read = 0
        for item in sorted(report.raw_evidence, key=lambda r: r.digest)[:max_attachments]:
            if read + item.size > max_raw_bytes:
                row = AttachmentAudit(digest=item.digest, size=item.size, status="BUDGET_EXCEEDED")
            elif raw_fd is None:
                row = AttachmentAudit(digest=item.digest, size=item.size, status=raw_status)
            else:
                row = _attachment(raw_fd, item.digest, item.size)
            rows.append(row)
            read += row.bytes_read
    finally:
        if raw_fd is not None:
            os.close(raw_fd)
        if parent_fd is not None:
            os.close(parent_fd)
    try:
        unchanged = read_report_bytes(path, max_bytes=len(raw)) == raw
    except InvalidInput:
        unchanged = False
    count = len(report.raw_evidence)
    verified = sum(row.status == "VERIFIED" for row in rows)
    complete = unchanged and pin_matches is not False and count == verified
    return ReportAudit(
        report_sha256=digest,
        artifact_digest=report.manifest_digest,
        semantic_digest=report.semantic_digest,
        status="VERIFIED" if complete else "INCOMPLETE",
        report_pin_matches=pin_matches,
        report_unchanged=unchanged,
        declared_attachments=count,
        verified_attachments=verified,
        unresolved_attachments=count - verified,
        omitted_attachments=count - len(rows),
        raw_bytes_read=sum(row.bytes_read for row in rows),
        attachments=tuple(rows),
    )


def verify_report(
    path: Path,
    *,
    expected_report_sha256: str | None = None,
    max_raw_bytes: int = MAX_RAW_BYTES,
    max_attachments: int = MAX_ATTACHMENTS,
) -> ReportAudit:
    return _audit_captured(
        path,
        read_report_bytes(path),
        expected_report_sha256=expected_report_sha256,
        max_raw_bytes=max_raw_bytes,
        max_attachments=max_attachments,
    )
