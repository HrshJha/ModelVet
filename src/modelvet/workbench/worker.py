"""Single-threaded own-code worker; model bytes are never deserialized."""

import json
import os
import signal
import sys
import tempfile
from pathlib import Path
from typing import Any

from modelvet.application.scan import ScanRequest, ScanService
from modelvet.core.errors import InvalidInput
from modelvet.core.json_data import strict_json
from modelvet.core.limits import MIB, ScanLimits
from modelvet.inventory.gate import InputGate, has_ancestor_identity, open_directory
from modelvet.workbench.models import ScanInput
from modelvet.workbench.paths import read_private, relative_path


def emit(kind: str, **data: Any) -> None:
    print(json.dumps({"type": kind, **data}, separators=(",", ":")), flush=True)


def main() -> int:
    if len(sys.argv) != 2:
        return 40
    os.umask(0o077)
    try:
        descriptor = strict_json(read_private(Path(sys.argv[1]), 65536), 65536)
        request = ScanInput.model_validate(descriptor["request"])
        workspace = Path(descriptor["workspace"])
        root = Path(descriptor["models_root"])
        for path, expected in (
            (workspace, descriptor["workspace_identity"]),
            (root, descriptor["model_identity"]),
        ):
            fd = open_directory(path)
            try:
                info = os.fstat(fd)
                if [info.st_dev, info.st_ino] != expected:
                    raise InvalidInput("Worker input root identity changed.")
            finally:
                os.close(fd)
        artifact = root / relative_path(request.model_path)
        fd = open_directory(artifact)
        try:
            if not has_ancestor_identity(fd, *descriptor["model_identity"]):
                raise InvalidInput("Worker artifact escapes the selected root.")
        finally:
            os.close(fd)
        staging = workspace / "staging" / descriptor["id"]
        tempfile.tempdir = str(staging)
        parent = descriptor["parent_pid"]

        def parent_alive(signum: int, frame: Any) -> None:
            if os.getppid() != parent:
                signal.setitimer(signal.ITIMER_REAL, 0)
                raise KeyboardInterrupt

        def interrupt(signum: int, frame: Any) -> None:
            signal.setitimer(signal.ITIMER_REAL, 0)
            raise KeyboardInterrupt

        signal.signal(signal.SIGALRM, parent_alive)
        signal.signal(signal.SIGTERM, interrupt)
        signal.setitimer(signal.ITIMER_REAL, 0.25, 0.25)
        parent_alive(0, None)
        policy = (
            None
            if request.policy_id == "default"
            else workspace / "policies" / f"{request.policy_id}.toml"
        )
        if policy is not None:
            import hashlib

            if hashlib.sha256(read_private(policy, 65536)).hexdigest() != request.policy_id:
                raise InvalidInput("Worker policy identity changed.")
        limits = ScanLimits(
            max_files=request.max_files,
            max_file_bytes=request.max_file_mib * MIB,
            max_total_bytes=request.max_total_mib * MIB,
            timeout_s=request.timeout_sec,
        )
        output = workspace / "reports" / descriptor["id"]
        InputGate().validate(artifact, output, limits)
        outcome = ScanService().run(
            ScanRequest(artifact, output, policy, request.scanner, limits, True),
            on_progress=lambda stage: emit("stage", stage=stage),
            process_observer=lambda pid, active: emit("process", pid=pid, active=active),
        )
        emit("result", report_path=str(outcome.json_path.relative_to(workspace)))
        return 0
    except KeyboardInterrupt:
        try:
            emit("cancelled")
        except BrokenPipeError:
            pass
        return 130
    except Exception:
        try:
            emit("error", code="SCAN_FAILED")
        except BrokenPipeError:
            pass
        return 50
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == "__main__":
    raise SystemExit(main())
