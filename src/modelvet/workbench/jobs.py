"""Bounded own-module worker supervisor, separate from scanner execution."""

import logging
import os
import selectors
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid
from datetime import UTC, datetime

from modelvet.core.config import load_policy
from modelvet.core.errors import InvalidInput
from modelvet.core.json_data import strict_json
from modelvet.inventory.gate import open_directory
from modelvet.workbench.models import JobRecord, ScanInput
from modelvet.workbench.paths import read_private, relative_path, trusted_worker_path
from modelvet.workbench.store import Store, opaque_id

STAGES = {
    "validation",
    "hub_inventory",
    "hub_retrieval",
    "snapshot",
    "inventory",
    "structural",
    "metadata",
    "scanner",
    "policy",
    "integrity",
    "report",
}


class Busy(Exception):
    """One scan is already active."""


def signal_group(pid: int, sig: int) -> None:
    try:
        os.killpg(pid, sig)
    except ProcessLookupError:
        pass


class Jobs:
    def __init__(self, store: Store) -> None:
        self.store = store
        self.guard = threading.RLock()
        self.process: subprocess.Popen[bytes] | None = None
        self.thread: threading.Thread | None = None
        self.active_id: str | None = None
        self.started = 0.0
        self.cancel_at: float | None = None
        self.groups: set[int] = set()
        self.stopping = False
        for record in store.jobs():
            if record.status == "interrupted":
                self.cleanup(record.id)

    def cleanup(self, key: str) -> None:
        opaque_id(key)
        self.store.workspace.check()
        parent = open_directory(self.store.workspace.root / "staging")
        try:
            try:
                shutil.rmtree(key, dir_fd=parent)
            except FileNotFoundError:
                pass
        finally:
            os.close(parent)
        parent = open_directory(self.store.workspace.root / "tasks")
        try:
            try:
                os.unlink(f"{key}.json", dir_fd=parent)
            except FileNotFoundError:
                pass
        finally:
            os.close(parent)

    def start(self, request: ScanInput) -> JobRecord:
        with self.guard:
            if self.stopping or self.active_id is not None:
                raise Busy("A scan is already running or the workbench is stopping.")
            workspace = self.store.workspace
            if request.hub_url:
                from modelvet.hub.reference import selected_token

                selected_token(request.use_hf_token)
            else:
                workspace.model_path(request.model_path)
            if request.policy_id != "default":
                import hashlib

                if len(request.policy_id) != 64 or any(
                    c not in "0123456789abcdef" for c in request.policy_id
                ):
                    raise InvalidInput("Select a validated policy.")
                selected = workspace.root / "policies" / f"{request.policy_id}.toml"
                if hashlib.sha256(read_private(selected, 65536)).hexdigest() != request.policy_id:
                    raise InvalidInput("Selected policy changed.")
                load_policy(selected)
            key = uuid.uuid4().hex
            stage = workspace.root / "staging" / key
            stage.mkdir(mode=0o700)
            record = JobRecord(
                id=key,
                model_path=None if request.hub_url else request.model_path,
                hub_url=request.hub_url,
                label=request.hub_url
                or (
                    workspace.models_root.name if request.model_path == "." else request.model_path
                ),
                status="running",
                stage="validation",
                started_at=datetime.now(UTC).isoformat(),
            )
            try:
                self.store.save_job(record)
                task = self.store.descriptor(
                    key,
                    {
                        "id": key,
                        "workspace": str(workspace.root),
                        "workspace_identity": workspace.identity,
                        "models_root": str(workspace.models_root),
                        "model_identity": workspace.model_identity,
                        "parent_pid": os.getpid(),
                        "request": request.model_dump(),
                    },
                )
                environment = {
                    "PATH": trusted_worker_path(workspace),
                    "HOME": str(stage),
                    "TMPDIR": str(stage),
                    "PYTHONUTF8": "1",
                    "PYTHONNOUSERSITE": "1",
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "LC_ALL": "C",
                    "OPENBLAS_NUM_THREADS": "1",
                    "OMP_NUM_THREADS": "1",
                }
                if request.hub_url and request.use_hf_token:
                    from modelvet.hub.reference import selected_token

                    environment["HF_TOKEN"] = selected_token(True) or ""
                # Fixed own-module worker; argv/descriptor contract tested independently.
                process = subprocess.Popen(  # noqa: S603 - trusted installed module, not artifact code.
                    (sys.executable, "-I", "-m", "modelvet.workbench.worker", str(task)),
                    shell=False,
                    close_fds=True,
                    start_new_session=True,
                    cwd=stage,
                    env=environment,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            except Exception:
                record.status, record.error_code = "failed", "WORKER_UNAVAILABLE"
                try:
                    self.store.save_job(record)
                except Exception:
                    logging.getLogger(__name__).error("Worker setup state could not be saved.")
                finally:
                    self.cleanup(key)
                raise
            self.process, self.active_id = process, key
            self.started, self.cancel_at = time.monotonic(), None
            self.groups.clear()
            self.thread = threading.Thread(
                target=self.collect,
                args=(record, process),
                daemon=True,
                name="modelvet-scan-supervisor",
            )
            try:
                self.thread.start()
            except RuntimeError:
                try:
                    self.cancel(key)
                    self.collect(record, process)
                    failed = self.store.job(key)
                    failed.status, failed.error_code = "failed", "SUPERVISOR_UNAVAILABLE"
                    self.store.save_job(failed)
                finally:
                    self.thread = None
                raise
            return record

    def current(self, key: str) -> JobRecord:
        record = self.store.job(key)
        with self.guard:
            if key == self.active_id:
                record.elapsed_seconds = round(time.monotonic() - self.started, 2)
        return record

    def cancel(self, key: str) -> JobRecord:
        with self.guard:
            if key != self.active_id or self.process is None:
                raise Busy("This job has already finished.")
            record = self.store.job(key)
            if self.cancel_at is None:
                self.cancel_at = time.monotonic()
                record.status = "cancelling"
                self.store.save_job(record)
                signal_group(self.process.pid, signal.SIGINT)
            return record

    def force_stop(self, process: subprocess.Popen[bytes]) -> None:
        with self.guard:
            for pid in self.groups:
                signal_group(pid, signal.SIGKILL)
            signal_group(process.pid, signal.SIGKILL)

    def collect(self, record: JobRecord, process: subprocess.Popen[bytes]) -> None:
        result_path: str | None = None
        error: str | None = None
        pending = bytearray()
        total = 0
        try:
            with selectors.DefaultSelector() as selector:
                if process.stdout is None or process.stderr is None:
                    raise InvalidInput("Worker streams unavailable.")
                selector.register(process.stdout, selectors.EVENT_READ, "stdout")
                selector.register(process.stderr, selectors.EVENT_READ, "stderr")
                while selector.get_map():
                    if time.monotonic() - self.started > 600:
                        error = "JOB_TIMEOUT"
                        self.cancel(record.id)
                    if self.cancel_at is not None and time.monotonic() - self.cancel_at > 5:
                        self.force_stop(process)
                    for key, _ in selector.select(0.1):
                        chunk = os.read(key.fd, 4096)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        total += len(chunk)
                        if total > 128 * 1024:
                            raise InvalidInput("Worker output exceeded its bound.")
                        if key.data == "stderr":
                            continue
                        pending.extend(chunk)
                        while b"\n" in pending:
                            raw, _, rest = pending.partition(b"\n")
                            pending = bytearray(rest)
                            event = strict_json(bytes(raw), 4096, max_tokens=100)
                            if not isinstance(event, dict):
                                raise InvalidInput("Invalid worker event.")
                            kind = event.get("type")
                            if kind == "stage" and event.get("stage") in STAGES:
                                current = self.store.job(record.id)
                                current.stage = event["stage"]
                                current.elapsed_seconds = round(time.monotonic() - self.started, 2)
                                self.store.save_job(current)
                            elif (
                                kind == "process"
                                and type(event.get("pid")) is int
                                and event["pid"] > 1
                                and type(event.get("active")) is bool
                            ):
                                with self.guard:
                                    if event["active"]:
                                        self.groups.add(event["pid"])
                                    else:
                                        self.groups.discard(event["pid"])
                            elif kind == "result" and isinstance(event.get("report_path"), str):
                                result_path = event["report_path"]
                            elif kind == "error":
                                code = event.get("code")
                                error = (
                                    code
                                    if code
                                    in {
                                        "HUB_ACCESS_FAILED",
                                        "SCAN_FAILED",
                                        "BUDGET_EXCEEDED",
                                        "INVALID_INPUT",
                                        "IDENTITY_DRIFT",
                                        "REPORT_WRITE_FAILED",
                                    }
                                    else "SCAN_FAILED"
                                )
                            elif kind != "cancelled":
                                raise InvalidInput("Unknown worker event.")
                        if len(pending) > 4096:
                            raise InvalidInput("Worker event exceeded its bound.")
            code = process.wait(timeout=5)
            with self.guard:
                current = self.store.job(record.id)
                current.elapsed_seconds = round(time.monotonic() - self.started, 2)
                if self.cancel_at is not None or code == 130:
                    current.status = "failed" if error == "JOB_TIMEOUT" else "cancelled"
                    current.error_code = error
                elif code == 0 and result_path is not None and error is None:
                    relative = relative_path(result_path)
                    if relative.parts[:2] != ("reports", record.id):
                        raise InvalidInput("Worker selected an unexpected report path.")
                    self.store.add_report(
                        self.store.workspace.root / relative,
                        record.label,
                        key=record.id,
                        model_path=record.model_path,
                    )
                    current.status, current.stage, current.report_id = (
                        "completed",
                        "complete",
                        record.id,
                    )
                else:
                    current.status, current.error_code = "failed", error or "WORKER_FAILED"
                self.force_stop(process)
                self.cleanup(record.id)
                self.store.save_job(current)
        except Exception:
            self.force_stop(process)
            process.wait(timeout=5)
            try:
                current = self.store.job(record.id)
                current.status, current.error_code = "failed", "WORKER_PROTOCOL_OR_STORAGE"
                current.report_id = None
                self.store.save_job(current)
            except Exception:
                # A broken index cannot record completion; recovery marks it interrupted.
                logging.getLogger(__name__).error("Job state unavailable; completion not recorded.")
        finally:
            self.force_stop(process)
            process.wait(timeout=5)
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()
            try:
                self.cleanup(record.id)
            finally:
                with self.guard:
                    self.active_id, self.process = None, None
                    self.groups.clear()

    def close(self) -> None:
        with self.guard:
            self.stopping = True
            if self.active_id is not None:
                self.cancel(self.active_id)
        if self.thread is not None:
            self.thread.join(timeout=12)
            if self.thread.is_alive():
                raise RuntimeError("Worker cleanup has not completed.")
