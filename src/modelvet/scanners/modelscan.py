"""Version-specific ModelScan CLI adapter; raw data is never a policy decision."""

import hashlib
import os
import shutil
import stat
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from modelvet.core.errors import InvalidInput
from modelvet.core.json_data import strict_json
from modelvet.core.snapshot import Snapshot
from modelvet.inventory.discover import stat_identity
from modelvet.inventory.gate import InputGate, open_directory
from modelvet.inventory.identity import InventoryService
from modelvet.scanners.base import RawScannerExecution, ScannerStatus, ToolInfo, ToolUnavailable
from modelvet.scanners.process import ProcessResult, run_bounded

PINNED_MODELSCAN_VERSION = "0.8.8"
MAX_RAW_REPORT = 4 * 1024 * 1024


def _binary_digest(path: Path) -> str:
    with path.open("rb") as stream:
        raw = stream.read(16 * 1024 * 1024 + 1)
    if len(raw) > 16 * 1024 * 1024:
        raise InvalidInput("Scanner entry point exceeds the reviewed size ceiling.")
    return hashlib.sha256(raw).hexdigest()


def _report_bytes(path: Path) -> bytes:
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return b""
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > MAX_RAW_REPORT:
            raise InvalidInput("Unsafe or oversized scanner report.")
        data = stream.read(MAX_RAW_REPORT + 1)
        if (
            len(data) > MAX_RAW_REPORT
            or info.st_size != len(data)
            or stat_identity(os.fstat(stream.fileno())) != stat_identity(info)
        ):
            raise InvalidInput("Scanner report changed or exceeded the output cap.")
        return data


class ModelScanAdapter:
    id = "modelscan"

    def __init__(self, executable: Path | None = None, output_limit: int = 1024 * 1024) -> None:
        self.executable = executable
        self.output_limit = output_limit

    def _executable(self) -> Path | None:
        found = str(self.executable) if self.executable is not None else shutil.which("modelscan")
        return Path(found).resolve(strict=True) if found else None

    def probe(self) -> ToolInfo | ToolUnavailable:
        try:
            binary = self._executable()
            if binary is None or not binary.is_file() or not os.access(binary, os.X_OK):
                return ToolUnavailable("ModelScan executable unavailable.")
            digest = _binary_digest(binary)
            with tempfile.TemporaryDirectory(prefix="modelvet-probe-") as directory:
                result = run_bounded(
                    (str(binary), "--version"), Path(directory), 5, self.output_limit
                )
            if result.failure or result.exit_code != 0:
                return ToolUnavailable("ModelScan version probe failed.")
            expected = f"modelscan, version {PINNED_MODELSCAN_VERSION}".encode()
            if result.stdout.strip() != expected or _binary_digest(binary) != digest:
                return ToolUnavailable("ModelScan version or entry-point identity mismatch.")
            return ToolInfo(
                self.id,
                PINNED_MODELSCAN_VERSION,
                f"pypi:modelscan=={PINNED_MODELSCAN_VERSION}",
                digest,
            )
        except (OSError, ValueError, InvalidInput, subprocess.SubprocessError):
            return ToolUnavailable("ModelScan probe could not enforce its process contract.")

    def run(self, snapshot: Snapshot, timeout_s: int, workdir: Path) -> RawScannerExecution:
        manifest = InventoryService().collect(snapshot)
        try:
            executable = self._executable()
            if executable is not None:
                InputGate().validate(
                    snapshot.source.artifact_dir, executable.parent, snapshot.source.limits
                )
                InputGate().validate(snapshot.root, executable.parent, snapshot.source.limits)
            if executable is not None and (
                executable.is_relative_to(snapshot.source.artifact_dir)
                or executable.is_relative_to(snapshot.root)
            ):
                return RawScannerExecution(
                    manifest.manifest_digest,
                    None,
                    "NOT_RUN",
                    reason="Scanner executable must be outside the untrusted artifact.",
                )
        except (OSError, InvalidInput):
            return RawScannerExecution(
                manifest.manifest_digest, None, "NOT_RUN", reason="Scanner executable unavailable."
            )
        tool = self.probe()
        if isinstance(tool, ToolUnavailable):
            return RawScannerExecution(
                manifest.manifest_digest, None, "NOT_RUN", reason=tool.reason
            )
        started = datetime.now(UTC).isoformat()
        argv: tuple[str, ...] = ()
        raw = b""
        result: ProcessResult | None = None
        try:
            InputGate().validate(snapshot.source.artifact_dir, workdir, snapshot.source.limits)
            InputGate().validate(snapshot.root, workdir, snapshot.source.limits)
            parent = open_directory(workdir)
            try:
                info = os.fstat(parent)
                if stat.S_IMODE(info.st_mode) & 0o077:
                    raise InvalidInput("Scanner work directory must be owner-only.")
            finally:
                os.close(parent)
            if workdir.is_relative_to(snapshot.root) or workdir.is_relative_to(
                snapshot.source.artifact_dir
            ):
                raise InvalidInput("Scanner workspace must be outside artifact/snapshot.")
            binary = self._executable()
            if binary is None or _binary_digest(binary) != tool.binary_sha256:
                raise InvalidInput("Scanner entry point changed before launch.")
            with tempfile.TemporaryDirectory(prefix="modelvet-scanner-", dir=workdir) as directory:
                private = Path(directory)
                target = private / "modelscan.json"
                argv = (
                    str(binary),
                    "-p",
                    str(snapshot.root),
                    "--reporting-format",
                    "json",
                    "--show-skipped",
                    "--output-file",
                    str(target),
                )
                result = run_bounded(argv, private, timeout_s, self.output_limit)
                raw = _report_bytes(target)
            statuses: dict[int, ScannerStatus] = {
                0: "COMPLETE",
                1: "COMPLETE",
                2: "FAILED",
                3: "UNSUPPORTED",
                4: "FAILED",
            }
            status = statuses.get(result.exit_code, "FAILED")
            reason = result.failure
            if result.failure or _binary_digest(binary) != tool.binary_sha256:
                status, reason = "FAILED", result.failure or "Scanner entry point changed."
            if status == "COMPLETE":
                if not raw or not isinstance(strict_json(raw, MAX_RAW_REPORT), dict):
                    raise InvalidInput("Missing or malformed ModelScan JSON.")
            return RawScannerExecution(
                manifest.manifest_digest,
                tool,
                status,
                argv,
                result.exit_code,
                result.stdout,
                result.stderr,
                raw,
                reason,
                started,
                datetime.now(UTC).isoformat(),
                result.environment_digest,
            )
        except (OSError, ValueError, InvalidInput, subprocess.SubprocessError):
            return RawScannerExecution(
                manifest.manifest_digest,
                tool,
                "FAILED",
                argv,
                exit_code=result.exit_code if result else None,
                stdout=result.stdout if result else b"",
                stderr=result.stderr if result else b"",
                report=raw,
                reason="Scanner process/report contract failed.",
                started_at=started,
                ended_at=datetime.now(UTC).isoformat(),
                environment_digest=result.environment_digest if result else None,
            )
