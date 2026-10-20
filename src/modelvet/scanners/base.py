"""Raw scanner contracts, separate from normalized evidence and policy."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from modelvet.core.snapshot import Snapshot
from modelvet.scanners.process import PROCESS_LIMITATIONS

ScannerStatus = Literal["COMPLETE", "FAILED", "UNSUPPORTED", "NOT_RUN"]


@dataclass(frozen=True)
class ToolInfo:
    tool_id: str
    version: str
    source: str
    binary_sha256: str


@dataclass(frozen=True)
class ToolUnavailable:
    reason: str


@dataclass(frozen=True)
class RawScannerExecution:
    artifact_digest: str
    tool: ToolInfo | None
    status: ScannerStatus
    argv: tuple[str, ...] = ()
    exit_code: int | None = None
    stdout: bytes = b""
    stderr: bytes = b""
    report: bytes = b""
    reason: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    environment_digest: str | None = None
    limitations: tuple[str, ...] = (
        "External scanner subprocess is not a sandbox; OS network isolation is not enforced.",
    ) + PROCESS_LIMITATIONS


class ScannerAdapter(Protocol):
    @property
    def id(self) -> str: ...
    def probe(self) -> ToolInfo | ToolUnavailable: ...
    def run(self, snapshot: Snapshot, timeout_s: int, workdir: Path) -> RawScannerExecution: ...
