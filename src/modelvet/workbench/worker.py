"""Single-threaded own-code worker; model bytes are never deserialized."""

import json
import os
import signal
import sys
import tempfile
from pathlib import Path
from typing import Any

from modelvet.application.scan import ScanRequest, ScanService
from modelvet.core.errors import BudgetExceeded, InvalidInput, SnapshotChanged
from modelvet.core.json_data import strict_json
from modelvet.core.limits import MIB, ScanLimits
from modelvet.inventory.gate import InputGate, has_ancestor_identity, open_directory
from modelvet.reports.writer import ReportWriteError
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
        artifact = None
        if not request.hub_url:
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
        if request.hub_url:
            from modelvet.hub.assessment import scan_hub

            outcome = scan_hub(
                request.hub_url,
                revision=request.revision,
                use_hf_token=request.use_hf_token,
                output_dir=output,
                policy_path=policy,
                scanner=request.scanner,
                limits=limits,
                on_progress=lambda stage: emit("stage", stage=stage),
                process_observer=lambda pid, active: emit("process", pid=pid, active=active),
            )
        else:
            if artifact is None:
                raise InvalidInput("Local artifact selection is missing.")
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
    except Exception as error:
        from modelvet.hub.transport import HubError

        code = (
            "HUB_ACCESS_FAILED"
            if isinstance(error, HubError)
            else "BUDGET_EXCEEDED"
            if isinstance(error, BudgetExceeded)
            else "IDENTITY_DRIFT"
            if isinstance(error, SnapshotChanged)
            else "INVALID_INPUT"
            if isinstance(error, InvalidInput)
            else "REPORT_WRITE_FAILED"
            if isinstance(error, ReportWriteError)
            else "SCAN_FAILED"
        )
        try:
            emit("error", code=code)
        except BrokenPipeError:
            pass
        return 50
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == "__main__":
    raise SystemExit(main())
