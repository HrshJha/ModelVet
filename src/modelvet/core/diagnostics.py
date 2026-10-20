"""Local capability probes without opening or loading model artifacts."""

import os
import platform
import stat
import tempfile
from pathlib import Path
from typing import Any

from modelvet.core.errors import InvalidInput
from modelvet.inventory.gate import open_directory
from modelvet.scanners.base import ToolUnavailable
from modelvet.scanners.modelscan import ModelScanAdapter
from modelvet.scanners.process import PROCESS_LIMITATIONS


def diagnose() -> dict[str, Any]:
    temporary_private = False
    output_writable = False
    try:
        with tempfile.TemporaryDirectory(prefix="modelvet-doctor-") as directory:
            temporary_private = stat.S_IMODE(os.stat(directory).st_mode) == 0o700
            with open(Path(directory) / "probe", "xb") as stream:
                stream.write(b"private capability probe")
        output = Path.home() / ".local/state/modelvet/reports"
        descriptor = open_directory(output, allow_missing=True)
        try:
            info = os.fstat(descriptor)
            output_writable = info.st_uid == os.geteuid() and bool(info.st_mode & stat.S_IWUSR)
        finally:
            os.close(descriptor)
    except (OSError, InvalidInput):
        pass
    scanner = ModelScanAdapter().probe()
    available = not isinstance(scanner, ToolUnavailable)
    supported = platform.system() in {"Linux", "Darwin"} and platform.python_version_tuple()[
        :2
    ] == ("3", "12")
    return {
        "python_version": platform.python_version(),
        "platform": platform.system(),
        "supported_platform": supported,
        "secure_paths_available": hasattr(os, "O_NOFOLLOW") and os.open in os.supports_dir_fd,
        "temporary_private": temporary_private,
        "output_ancestor_writable": output_writable,
        "scanner_available": available,
        "scanner_version": None if isinstance(scanner, ToolUnavailable) else scanner.version,
        "scanner_reason": scanner.reason if isinstance(scanner, ToolUnavailable) else None,
        "serialized_scan_ready": available
        and not PROCESS_LIMITATIONS
        and supported
        and temporary_private
        and output_writable,
        "limitations": [
            "Scanner subprocess is not a sandbox; OS network isolation is not enforced.",
            *PROCESS_LIMITATIONS,
        ],
    }
