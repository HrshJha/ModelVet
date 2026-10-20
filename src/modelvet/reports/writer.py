"""Descriptor-based private non-overwriting writes; JSON is the commit marker."""

import hashlib
import os
import shutil
from pathlib import Path

from modelvet.core.errors import InvalidInput
from modelvet.core.limits import ScanLimits
from modelvet.inventory.gate import InputGate, absolute_path
from modelvet.reports.json_report import Report, serialize_report
from modelvet.reports.markdown import render_markdown


class ReportWriteError(Exception):
    """No completed report could be safely published."""


def _directory(path: Path) -> int:
    descriptor = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parts[1:]:
            try:
                os.mkdir(part, 0o700, dir_fd=descriptor)
            except FileExistsError:
                pass
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _atomic(fd: int, name: str, payload: bytes) -> None:
    temporary = "." + name + ".tmp"
    descriptor = os.open(
        temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd
    )
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    # linkat is atomic and refuses an existing destination, unlike replace().
    os.link(temporary, name, src_dir_fd=fd, dst_dir_fd=fd, follow_symlinks=False)
    os.unlink(temporary, dir_fd=fd)


class ReportWriter:
    def write(
        self,
        report: Report,
        output_dir: Path,
        *,
        artifact_dir: Path,
        snapshot_dir: Path | None = None,
        raw_payloads: dict[str, bytes] | None = None,
        markdown: bool = True,
    ) -> tuple[Path, Path | None]:
        output = absolute_path(output_dir)
        InputGate().validate(artifact_dir, output, ScanLimits())
        if output.is_relative_to(absolute_path(artifact_dir)) or (
            snapshot_dir and output.is_relative_to(absolute_path(snapshot_dir))
        ):
            raise InvalidInput("Reports must be outside artifact and snapshot directories.")
        raw = raw_payloads or {}
        if set(raw) != {r.digest for r in report.raw_evidence} or any(
            hashlib.sha256(value).hexdigest() != key
            or len(value) != next(r.size for r in report.raw_evidence if r.digest == key)
            for key, value in raw.items()
        ):
            raise ReportWriteError("Raw evidence is missing or changed before writing.")
        encoded = serialize_report(report)
        parent = run_fd = None
        created = False
        group = output / report.manifest_digest.split(":")[1][:12]
        run_dir = group / report.run.run_id
        try:
            parent = _directory(group)
            os.mkdir(report.run.run_id, 0o700, dir_fd=parent)
            created = True
            run_fd = os.open(
                report.run.run_id, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent
            )
            if raw:
                os.mkdir("raw", 0o700, dir_fd=run_fd)
                raw_fd = os.open("raw", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=run_fd)
                try:
                    for digest, value in sorted(raw.items()):
                        _atomic(raw_fd, digest + ".bin", value)
                    os.fsync(raw_fd)
                finally:
                    os.close(raw_fd)
            if markdown:
                _atomic(run_fd, "report.md", render_markdown(report).encode())
            _atomic(run_fd, "report.json", encoded)
            os.fsync(run_fd)
            os.fsync(parent)
            return run_dir / "report.json", run_dir / "report.md" if markdown else None
        except (OSError, ValueError) as exc:
            raise ReportWriteError("Could not publish a complete private report.") from exc
        finally:
            import sys

            failed = sys.exc_info()[0] is not None
            if run_fd is not None:
                os.close(run_fd)
            if failed and created and parent is not None:
                shutil.rmtree(report.run.run_id, dir_fd=parent)
            if parent is not None:
                os.close(parent)
