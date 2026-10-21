"""Remote orchestration in front of the unchanged local static engine."""

import logging
import signal
import tempfile
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from types import FrameType
from typing import Literal

from modelvet.application.scan import ScanOutcome, ScanRequest, ScanService
from modelvet.core.errors import InvalidInput
from modelvet.core.limits import ScanLimits
from modelvet.hub.reference import HubReference, selected_token
from modelvet.hub.retrieval import HubLimits, retrieve
from modelvet.hub.transport import HTTPS, HubError
from modelvet.inventory.gate import InputGate


@contextmanager
def assessment_deadline(seconds: float) -> Iterator[None]:
    if threading.current_thread() is not threading.main_thread():
        raise InvalidInput("Run Hub assessment in a dedicated worker process.")
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    deadline = time.monotonic() + seconds

    def check(signum: int, frame: FrameType | None) -> None:
        if time.monotonic() >= deadline:
            raise HubError("Hugging Face assessment wall-time limit reached.")
        if callable(previous_handler):
            previous_handler(signum, frame)

    signal.signal(signal.SIGALRM, check)
    signal.setitimer(signal.ITIMER_REAL, min(0.25, seconds), 0.25)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        signal.setitimer(signal.ITIMER_REAL, *previous_timer)


def scan_hub(
    url: str,
    *,
    revision: str | None = None,
    use_hf_token: bool = False,
    output_dir: Path | None = None,
    policy_path: Path | None = None,
    scanner: Literal["auto", "modelscan", "none"] = "auto",
    limits: ScanLimits | None = None,
    markdown: bool = True,
    on_progress: Callable[[str], None] | None = None,
    process_observer: Callable[[int, bool], None] | None = None,
) -> ScanOutcome:
    limits = limits or ScanLimits()
    reference = HubReference.parse(url, revision)
    transfer_limits = HubLimits(limits.max_files, limits.max_file_bytes, limits.max_total_bytes)
    token = selected_token(use_hf_token)

    def progress(stage: str) -> None:
        if on_progress is not None:
            try:
                on_progress(stage)
            except Exception:
                logging.getLogger(__name__).warning("Hub progress observer unavailable.")

    progress("hub_inventory")
    transport = HTTPS(token=token, wall_time_s=transfer_limits.wall_time_s)
    with (
        assessment_deadline(transfer_limits.wall_time_s),
        tempfile.TemporaryDirectory(prefix="modelvet-hub-") as directory,
    ):
        root = Path(directory).resolve()
        InputGate().validate(root, output_dir, limits)
        # Inventory happens before the first byte of model content is transferred.
        source = retrieve(reference, root, transfer_limits, transport, on_progress=progress)
        transport.token = None
        return ScanService().run(
            ScanRequest(root, output_dir, policy_path, scanner, limits, markdown),
            remote_source=source,
            on_progress=progress,
            process_observer=process_observer,
        )
