import hashlib
import os
import stat
from pathlib import Path

import pytest

from modelvet.core.errors import InvalidInput, SnapshotChanged
from modelvet.core.limits import ScanLimits
from modelvet.core.snapshot import Snapshotter
from modelvet.inventory.discover import validate_relpath
from modelvet.inventory.gate import InputGate


def test_snapshot_is_private_bounded_and_cleaned(tmp_path: Path) -> None:
    source = tmp_path / "input"
    (source / "nested").mkdir(parents=True)
    (source / "nested/data").write_bytes(b"inert bytes")
    valid = InputGate().validate(source, tmp_path / "out", ScanLimits())
    with Snapshotter(tmp_path).create(valid) as snapshot:
        root = snapshot.root
        assert stat.S_IMODE(root.stat().st_mode) == 0o700
        (entry,) = snapshot.files
        assert entry.relpath == "nested/data"
        assert entry.sha256 == hashlib.sha256(b"inert bytes").hexdigest()
        assert (root / entry.relpath).read_bytes() == b"inert bytes"
        assert stat.S_IMODE((root / entry.relpath).stat().st_mode) == 0o400
    assert not root.exists()
    assert (source / "nested/data").read_bytes() == b"inert bytes"


@pytest.mark.parametrize("kind", ["symlink", "directory-link", "hardlink", "fifo"])
def test_reject_special_nodes_and_cleanup(tmp_path: Path, kind: str) -> None:
    source = tmp_path / "input"
    source.mkdir()
    existing = tmp_path / "existing"
    existing.write_bytes(b"never executed")
    target = source / "target"
    if kind == "symlink":
        target.symlink_to(existing)
    elif kind == "directory-link":
        target.symlink_to(tmp_path, target_is_directory=True)
    elif kind == "hardlink":
        target.hardlink_to(existing)
    else:
        os.mkfifo(target)
    staging = tmp_path / "staging"
    staging.mkdir()
    valid = InputGate().validate(source, tmp_path / "out", ScanLimits())
    with pytest.raises(InvalidInput), Snapshotter(staging).create(valid):
        pytest.fail("Unsafe snapshot yielded")
    assert list(staging.iterdir()) == []
    assert existing.read_bytes() == b"never executed"


@pytest.mark.parametrize(
    "limits", [ScanLimits(max_files=1), ScanLimits(max_file_bytes=2), ScanLimits(max_total_bytes=3)]
)
def test_resource_limits(tmp_path: Path, limits: ScanLimits) -> None:
    source = tmp_path / "input"
    source.mkdir()
    (source / "a").write_bytes(b"1234")
    (source / "b").write_bytes(b"5678")
    valid = InputGate().validate(source, tmp_path / "out", limits)
    with pytest.raises(InvalidInput), Snapshotter(tmp_path).create(valid):
        pytest.fail("Over-budget snapshot yielded")


def test_mutation_during_copy_is_detected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "input"
    source.mkdir()
    data = source / "data"
    data.write_bytes(b"a" * 100)
    valid = InputGate().validate(source, tmp_path / "out", ScanLimits())
    read = os.read
    changed = False

    def racing_read(fd: int, count: int) -> bytes:
        nonlocal changed
        chunk = read(fd, count)
        if not changed:
            changed = True
            data.write_bytes(b"b" * 100)
        return chunk

    monkeypatch.setattr(os, "read", racing_read)
    with pytest.raises(SnapshotChanged), Snapshotter(tmp_path).create(valid):
        pytest.fail("Mutated snapshot yielded")


def test_root_replacement_after_gate_is_detected(tmp_path: Path) -> None:
    source = tmp_path / "input"
    source.mkdir()
    valid = InputGate().validate(source, tmp_path / "out", ScanLimits())
    source.rename(tmp_path / "old")
    source.mkdir()
    with pytest.raises(SnapshotChanged), Snapshotter(tmp_path).create(valid):
        pytest.fail("Replaced root yielded")


@pytest.mark.parametrize("name", ["../bad", "/absolute", "a\\b", "a\nb", "e\u0301", "a//b"])
def test_reject_ambiguous_names(name: str) -> None:
    with pytest.raises(InvalidInput):
        validate_relpath(name)


def test_cleanup_when_consumer_raises(tmp_path: Path) -> None:
    source = tmp_path / "input"
    source.mkdir()
    valid = InputGate().validate(source, tmp_path / "out", ScanLimits())
    with pytest.raises(RuntimeError), Snapshotter(tmp_path).create(valid) as snapshot:
        root = snapshot.root
        raise RuntimeError("controlled consumer failure")
    assert not root.exists()
