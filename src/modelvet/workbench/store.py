"""Private SQLite index; report bytes remain authoritative and pinned."""

import hashlib
import json
import os
import re
import sqlite3
import stat
import threading
import uuid
from pathlib import Path
from typing import Any

from modelvet.core.errors import InvalidInput
from modelvet.reports.json_report import MAX_REPORT_BYTES, Report, parse_report
from modelvet.workbench.guidance import summarize
from modelvet.workbench.models import JobRecord, ReportPage, ReportSummary
from modelvet.workbench.paths import Workspace, read_private, relative_path, write_private


def opaque_id(value: str) -> str:
    if not re.fullmatch(r"[a-f0-9]{32}", value):
        raise InvalidInput("Invalid workbench record identifier.")
    return value


class Store:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace
        self.lock = threading.RLock()
        self.path = workspace.root / "history.sqlite3"
        try:
            write_private(self.path, b"")
        except FileExistsError:
            pass
        self.identity: tuple[int, int] | None = None
        self._check()
        self.connection = sqlite3.connect(self.path, check_same_thread=False, timeout=2.5)
        self._check()
        self.connection.execute("PRAGMA trusted_schema=OFF")
        self.connection.execute("PRAGMA journal_mode=DELETE")
        self.connection.execute("PRAGMA temp_store=MEMORY")
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
        )
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS reports (id TEXT PRIMARY KEY, path "
            "TEXT NOT NULL, sha256 TEXT NOT NULL, summary TEXT NOT NULL)"
        )
        self.connection.commit()
        for record in self.jobs():
            if record.status in {"running", "cancelling"}:
                record.status = "interrupted"
                record.error_code = "SERVER_RESTARTED"
                self.save_job(record)

    def _check(self) -> None:
        self.workspace.check()
        fd = os.open(self.path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            info = os.fstat(fd)
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1
                or info.st_uid != os.geteuid()
                or stat.S_IMODE(info.st_mode) & 0o077
                or info.st_size > 128 * 1024**2
            ):
                raise InvalidInput("Unsafe or oversized history index.")
            identity = (info.st_dev, info.st_ino)
            if self.identity is not None and self.identity != identity:
                raise InvalidInput("History index identity changed.")
            self.identity = identity
        finally:
            os.close(fd)

    def close(self) -> None:
        with self.lock:
            self.connection.close()

    def query(self, sql: str, parameters: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
        with self.lock:
            self._check()
            with self.connection:
                return self.connection.execute(sql, parameters).fetchall()

    def save_job(self, record: JobRecord) -> None:
        opaque_id(record.id)
        self.query(
            "INSERT OR REPLACE INTO jobs VALUES (?, ?)", (record.id, record.model_dump_json())
        )

    def job(self, key: str) -> JobRecord:
        rows = self.query("SELECT payload FROM jobs WHERE id = ?", (opaque_id(key),))
        if not rows:
            raise InvalidInput("Job was not found.")
        return JobRecord.model_validate_json(rows[0][0])

    def jobs(self) -> list[JobRecord]:
        return [
            JobRecord.model_validate_json(row[0])
            for row in self.query("SELECT payload FROM jobs ORDER BY rowid DESC LIMIT 10000")
        ]

    def add_report(
        self, path: Path, label: str, *, key: str | None = None, model_path: str | None = None
    ) -> ReportSummary:
        self.workspace.check()
        selected = relative_path(str(path.relative_to(self.workspace.root)))
        if selected.parts[0] not in {"reports", "imports"}:
            raise InvalidInput("Report must be owned by this workspace.")
        raw = read_private(path, MAX_REPORT_BYTES)
        report = parse_report(raw)
        key = opaque_id(key or uuid.uuid4().hex)
        summary = summarize(report, key, label)
        summary.model_path = model_path
        self.query(
            "INSERT INTO reports VALUES (?, ?, ?, ?)",
            (key, str(selected), hashlib.sha256(raw).hexdigest(), summary.model_dump_json()),
        )
        return summary

    def report_path(self, key: str) -> Path:
        self.report(key)
        rows = self.query("SELECT path FROM reports WHERE id = ?", (opaque_id(key),))
        return self.workspace.root / relative_path(rows[0][0])

    def report(
        self, key: str, *, max_bytes: int = MAX_REPORT_BYTES
    ) -> tuple[Report, bytes, ReportSummary]:
        rows = self.query(
            "SELECT path, sha256, summary FROM reports WHERE id = ?", (opaque_id(key),)
        )
        if not rows:
            raise InvalidInput("Report was not found.")
        relative = relative_path(rows[0][0])
        if relative.parts[0] not in {"reports", "imports"}:
            raise InvalidInput("Invalid report storage path.")
        path = self.workspace.root / relative
        raw = read_private(path, max_bytes)
        if hashlib.sha256(raw).hexdigest() != rows[0][1]:
            raise InvalidInput("Stored report bytes changed.")
        report = parse_report(raw)
        cached = ReportSummary.model_validate_json(rows[0][2])
        summary = summarize(report, key, cached.label)
        summary.model_path = cached.model_path
        return report, raw, summary

    def reports(self, offset: int, limit: int) -> ReportPage:
        rows = self.query(
            "SELECT id FROM reports ORDER BY rowid DESC LIMIT ? OFFSET ?", (limit, offset)
        )
        count = self.query("SELECT COUNT(*) FROM reports")[0][0]
        items = []
        remaining = 128 * 1024**2
        for row in rows:
            _, raw, summary = self.report(row[0], max_bytes=min(MAX_REPORT_BYTES, remaining))
            remaining -= len(raw)
            items.append(summary)
        return ReportPage(
            items=items,
            total=count,
            offset=offset,
            limit=limit,
        )

    def import_report(self, raw: bytes) -> ReportSummary:
        parse_report(raw)
        key = uuid.uuid4().hex
        target = self.workspace.root / "imports" / f"{key}.json"
        write_private(target, raw)
        try:
            return self.add_report(target, "Imported report", key=key)
        except BaseException:
            target.unlink(missing_ok=True)
            raise

    def descriptor(self, key: str, data: dict[str, Any]) -> Path:
        target = self.workspace.root / "tasks" / f"{opaque_id(key)}.json"
        write_private(target, json.dumps(data, allow_nan=False).encode())
        return target
