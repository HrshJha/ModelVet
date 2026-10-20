"""Explicit-manifest stored-report auditing with shared finite byte budgets."""

import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import Field, ValidationError, field_validator, model_validator

from modelvet.core.errors import BudgetExceeded, InvalidInput
from modelvet.core.json_data import strict_json
from modelvet.evidence.models import SHA256, WireModel
from modelvet.inventory.discover import stat_identity, validate_relpath
from modelvet.inventory.gate import absolute_path, open_directory
from modelvet.reports.audit import MAX_RAW_BYTES, ReportAudit, _audit_captured
from modelvet.reports.json_report import MAX_REPORT_BYTES, parse_report, read_report_bytes

MAX_BATCH_REPORTS = 32
MAX_MANIFEST_BYTES = 64 * 1024
MAX_BATCH_JSON = 128 * 1024 * 1024
MAX_BATCH_RAW = 128 * 1024 * 1024


class BatchEntry(WireModel):
    path: Annotated[str, Field(min_length=1, max_length=4096)]
    expected_report_sha256: SHA256 | None = None

    @field_validator("path")
    @classmethod
    def relative(cls, value: str) -> str:
        return validate_relpath(value)


class BatchManifest(WireModel):
    schema_version: Literal["1.0.0"]
    reports: Annotated[tuple[BatchEntry, ...], Field(min_length=1, max_length=MAX_BATCH_REPORTS)]

    @model_validator(mode="after")
    def unique_paths(self) -> Self:
        if len({r.path.casefold() for r in self.reports}) != len(self.reports):
            raise ValueError("Duplicate or aliased report paths.")
        return self


class BatchRow(WireModel):
    index: Annotated[int, Field(ge=0, lt=MAX_BATCH_REPORTS)]
    path_digest: SHA256
    status: Literal["VERIFIED", "INCOMPLETE", "INVALID", "BUDGET_EXCEEDED"]
    report_bytes_charged: Annotated[int, Field(ge=0, le=2 * MAX_REPORT_BYTES)]
    audit: ReportAudit | None = None
    reason_code: Literal["REPORT_INVALID", "BUDGET_EXCEEDED"] | None = None

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if self.status in {"VERIFIED", "INCOMPLETE"}:
            if (
                self.audit is None
                or self.audit.status != self.status
                or self.reason_code is not None
            ):
                raise ValueError("Batch row must match its audit evidence.")
        elif self.audit is not None or self.reason_code != (
            "REPORT_INVALID" if self.status == "INVALID" else "BUDGET_EXCEEDED"
        ):
            raise ValueError("Unprocessed/invalid row cannot contain successful evidence.")
        return self


class BatchAudit(WireModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    manifest_sha256: SHA256
    manifest_unchanged: bool
    root_unchanged: bool
    status: Literal["VERIFIED", "INCOMPLETE"]
    verified_reports: Annotated[int, Field(ge=0, le=MAX_BATCH_REPORTS)]
    unresolved_reports: Annotated[int, Field(ge=0, le=MAX_BATCH_REPORTS)]
    report_bytes_charged: Annotated[int, Field(ge=0, le=MAX_BATCH_JSON)]
    raw_bytes_read: Annotated[int, Field(ge=0, le=MAX_BATCH_RAW)]
    rows: Annotated[tuple[BatchRow, ...], Field(min_length=1, max_length=MAX_BATCH_REPORTS)]
    admission_recomputed: Literal[False] = False
    notice: Literal[
        "Stored byte consistency only. Paths suppressed; no author authentication or admission."
    ] = "Stored byte consistency only. Paths suppressed; no author authentication or admission."

    @model_validator(mode="after")
    def coherent(self) -> Self:
        verified = sum(r.status == "VERIFIED" for r in self.rows)
        complete = verified == len(self.rows) and self.manifest_unchanged and self.root_unchanged
        if (
            [r.index for r in self.rows] != list(range(len(self.rows)))
            or len({r.path_digest for r in self.rows}) != len(self.rows)
            or self.verified_reports != verified
            or self.unresolved_reports != len(self.rows) - verified
            or self.report_bytes_charged != sum(r.report_bytes_charged for r in self.rows)
            or self.raw_bytes_read != sum(r.audit.raw_bytes_read for r in self.rows if r.audit)
            or (self.status == "VERIFIED") != complete
        ):
            raise ValueError("Batch aggregate cannot disagree with row evidence.")
        return self


def _manifest_bytes(path: Path) -> bytes:
    selected = absolute_path(path)
    try:
        parent = open_directory(selected.parent)
        try:
            fd = os.open(selected.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            with os.fdopen(fd, "rb") as stream:
                before = os.fstat(stream.fileno())
                if (
                    not stat.S_ISREG(before.st_mode)
                    or before.st_nlink != 1
                    or before.st_size > MAX_MANIFEST_BYTES
                ):
                    raise InvalidInput("Unsafe or oversized batch manifest.")
                raw = stream.read(before.st_size)
                if (
                    stat_identity(before) != stat_identity(os.fstat(stream.fileno()))
                    or len(raw) != before.st_size
                ):
                    raise InvalidInput("Batch manifest changed during read.")
                return raw
        finally:
            os.close(parent)
    except OSError as exc:
        raise InvalidInput("Cannot safely read batch manifest.") from exc


def audit_batch(
    manifest_path: Path,
    root: Path,
    *,
    max_report_bytes: int = MAX_BATCH_JSON,
    max_raw_bytes: int = MAX_BATCH_RAW,
) -> BatchAudit:
    if (
        type(max_report_bytes) is not int
        or not 0 <= max_report_bytes <= MAX_BATCH_JSON
        or type(max_raw_bytes) is not int
        or not 0 <= max_raw_bytes <= MAX_BATCH_RAW
    ):
        raise InvalidInput("Batch budgets must remain within hard ceilings.")
    raw = _manifest_bytes(manifest_path)
    try:
        manifest = BatchManifest.model_validate_json(
            json.dumps(strict_json(raw, MAX_MANIFEST_BYTES))
        )
    except (ValueError, ValidationError) as exc:
        raise InvalidInput("Invalid batch manifest schema or paths.") from exc
    selected_root = absolute_path(root)
    try:
        root_fd = open_directory(selected_root)
    except OSError as exc:
        raise InvalidInput("Batch report root is missing or unsafe.") from exc
    rows = []
    json_charged = raw_read = 0
    try:
        initial_root = os.fstat(root_fd)
        for index, entry in enumerate(manifest.reports):
            charge = 0
            audit = None
            reason: Literal["REPORT_INVALID", "BUDGET_EXCEEDED"] | None = None
            status: Literal["VERIFIED", "INCOMPLETE", "INVALID", "BUDGET_EXCEEDED"]
            try:
                remaining = max_report_bytes - json_charged
                if remaining < 2:
                    raise BudgetExceeded("Batch report read budget exhausted.")
                path = selected_root / entry.path
                captured = read_report_bytes(path, max_bytes=min(MAX_REPORT_BYTES, remaining // 2))
                charge = 2 * len(captured)  # Reserve validation + bounded identity recheck.
                json_charged += charge
                report = parse_report(captured)
                raw_needed = sum(r.size for r in report.raw_evidence)
                if raw_needed > min(MAX_RAW_BYTES, max_raw_bytes - raw_read):
                    raise BudgetExceeded("Batch raw evidence budget exhausted.")
                audit = _audit_captured(
                    path,
                    captured,
                    expected_report_sha256=entry.expected_report_sha256,
                    max_raw_bytes=min(MAX_RAW_BYTES, max_raw_bytes - raw_read),
                )
                raw_read += audit.raw_bytes_read
                status = audit.status
            except BudgetExceeded:
                status, reason = "BUDGET_EXCEEDED", "BUDGET_EXCEEDED"
            except InvalidInput:
                status, reason = "INVALID", "REPORT_INVALID"
            rows.append(
                BatchRow(
                    index=index,
                    path_digest=hashlib.sha256(entry.path.encode()).hexdigest(),
                    status=status,
                    report_bytes_charged=charge,
                    audit=audit,
                    reason_code=reason,
                )
            )
        try:
            current_fd = open_directory(selected_root)
            try:
                current_root = os.fstat(current_fd)
            finally:
                os.close(current_fd)
            root_unchanged = (initial_root.st_dev, initial_root.st_ino) == (
                current_root.st_dev,
                current_root.st_ino,
            )
        except OSError:
            root_unchanged = False
    finally:
        os.close(root_fd)
    try:
        manifest_unchanged = _manifest_bytes(manifest_path) == raw
    except InvalidInput:
        manifest_unchanged = False
    verified = sum(row.status == "VERIFIED" for row in rows)
    complete = verified == len(rows) and root_unchanged and manifest_unchanged
    return BatchAudit(
        manifest_sha256=hashlib.sha256(raw).hexdigest(),
        manifest_unchanged=manifest_unchanged,
        root_unchanged=root_unchanged,
        status="VERIFIED" if complete else "INCOMPLETE",
        verified_reports=verified,
        unresolved_reports=len(rows) - verified,
        report_bytes_charged=json_charged,
        raw_bytes_read=raw_read,
        rows=tuple(rows),
    )
