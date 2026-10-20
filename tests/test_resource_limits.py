import json
import os
import sys
import time
import tracemalloc
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from modelvet.core.errors import InvalidInput
from modelvet.core.limits import ScanLimits
from modelvet.core.snapshot import Snapshotter
from modelvet.inventory import discover
from modelvet.inventory.discover import observe_directory
from modelvet.inventory.gate import InputGate
from modelvet.inventory.identity import InventoryService
from modelvet.scanners.process import PROCESS_LIMITATIONS, run_bounded
from modelvet.structural.safetensors import SafetensorsInspector
from modelvet.structural.zip_index import ZipIndexInspector


def test_full_entry_limit_is_bounded_in_time_and_allocations(tmp_path) -> None:
    root = tmp_path / "input"
    root.mkdir()
    for i in range(10001):
        (root / f"file{i:05d}").touch()
    source = InputGate().validate(root, tmp_path / "out", ScanLimits())
    tracemalloc.start()
    started = time.monotonic()
    try:
        with pytest.raises(InvalidInput):
            observe_directory(source)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    elapsed = time.monotonic() - started
    print(
        json.dumps(
            {"case": "10001 empty files", "elapsed_s": round(elapsed, 4), "python_peak_bytes": peak}
        )
    )
    assert elapsed < 30 and peak < 64 * 1024 * 1024


def test_sparse_huge_file_rejected_without_reading_payload(tmp_path, monkeypatch) -> None:
    root = tmp_path / "input"
    root.mkdir()
    with (root / "huge.bin").open("wb") as stream:
        stream.truncate(1024**3 + 1)
    source = InputGate().validate(root, tmp_path / "out", ScanLimits())

    def forbidden(*args):
        raise AssertionError("Payload read before declared size cap")

    monkeypatch.setattr(discover.os, "read", forbidden)
    with pytest.raises(InvalidInput):
        observe_directory(source)


def test_total_byte_limit_reads_at_most_one_extra_byte(tmp_path, monkeypatch) -> None:
    root = tmp_path / "input"
    root.mkdir()
    (root / "bytes.bin").write_bytes(b"x" * 131072)
    source = InputGate().validate(root, tmp_path / "out", ScanLimits(max_total_bytes=65536))
    original = os.read
    counts = []

    def observed(fd, count):
        value = original(fd, count)
        counts.append((count, len(value)))
        return value

    monkeypatch.setattr(discover.os, "read", observed)
    with pytest.raises(InvalidInput):
        observe_directory(source)
    assert sum(length for _, length in counts) <= 65537
    assert max(count for count, _ in counts) <= 65536


@given(st.binary(max_size=4096))
@settings(
    max_examples=40, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_random_structural_bytes_do_not_escape_budgets(tmp_path, raw) -> None:
    root = tmp_path / "input"
    root.mkdir(exist_ok=True)
    (root / "data.safetensors").write_bytes(raw)
    source = InputGate().validate(root, tmp_path / "out", ScanLimits(max_metadata_bytes=4096))
    with Snapshotter().create(source) as snapshot:
        file = InventoryService().collect(snapshot).files[0]
        for inspector in (SafetensorsInspector(), ZipIndexInspector()):
            result = inspector.inspect(file, snapshot)
            assert result.status in {"COMPLETE", "FAILED", "UNSUPPORTED"}


def test_stat_to_open_symlink_swap_is_rejected(tmp_path, monkeypatch) -> None:
    root = tmp_path / "input"
    root.mkdir()
    target = root / "file.bin"
    target.write_bytes(b"inert")
    outside = tmp_path / "outside"
    outside.write_bytes(b"must not read")
    source = InputGate().validate(root, tmp_path / "out", ScanLimits())
    original = os.stat

    def swap(path, *args, **kwargs):
        result = original(path, *args, **kwargs)
        if path == "file.bin" and kwargs.get("follow_symlinks") is False:
            target.unlink()
            target.symlink_to(outside)
        return result

    monkeypatch.setattr(discover.os, "stat", swap)
    with pytest.raises(InvalidInput):
        observe_directory(source)
    assert outside.read_bytes() == b"must not read"


def test_failed_secure_opens_do_not_leak_descriptors(tmp_path) -> None:
    fd_root = Path("/dev/fd" if sys.platform == "darwin" else "/proc/self/fd")
    before = len(list(fd_root.iterdir()))
    for _ in range(100):
        with pytest.raises(InvalidInput):
            InputGate().validate(tmp_path / "missing", tmp_path / "out", ScanLimits())
    assert len(list(fd_root.iterdir())) <= before + 1


def test_scanner_wall_time_is_bounded(tmp_path) -> None:
    started = time.monotonic()
    result = run_bounded((sys.executable, "-c", "import time;time.sleep(30)"), tmp_path, 1)
    elapsed = time.monotonic() - started
    print(
        json.dumps(
            {"case": "scanner timeout", "elapsed_s": round(elapsed, 4), "failure": result.failure}
        )
    )
    assert result.failure == "TIMEOUT" and elapsed < 5


@pytest.mark.skipif(
    sys.platform != "linux", reason="Linux OS memory caps require a Linux execution environment"
)
def test_linux_scanner_memory_caps_are_applied(tmp_path) -> None:
    body = (
        "import resource,json; print(json.dumps(["
        "resource.getrlimit(resource.RLIMIT_AS),resource.getrlimit(resource.RLIMIT_DATA)]))"
    )
    result = run_bounded((sys.executable, "-c", body), tmp_path, 3)
    assert result.exit_code == 0
    assert json.loads(result.stdout) == [[2 * 1024**3] * 2] * 2


def test_darwin_memory_limit_is_disclosed() -> None:
    if sys.platform == "darwin":
        assert any("memory is not OS-bounded" in item for item in PROCESS_LIMITATIONS)
