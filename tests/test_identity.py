import hashlib
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from modelvet.core.errors import InvalidInput, SnapshotChanged
from modelvet.core.limits import ScanLimits
from modelvet.core.snapshot import Snapshotter
from modelvet.inventory.discover import FileObservation
from modelvet.inventory.gate import InputGate
from modelvet.inventory.identity import InventoryService, manifest_from_entries


def observation(path: str, content: bytes) -> FileObservation:
    return FileObservation(path, len(content), hashlib.sha256(content).hexdigest())


def test_manifest_v1_contract() -> None:
    item = observation("a.txt", b"abc")
    manifest = manifest_from_entries((item,))
    expected = hashlib.sha256(
        b"modelvet-manifest-v1\na.txt\x003\x00" + item.sha256.encode() + b"\n"
    ).hexdigest()
    assert manifest.manifest_digest == "sha256:" + expected
    assert (
        manifest.files[0].file_id
        == hashlib.sha256(b"modelvet-file-v1\0a.txt\0" + bytes.fromhex(item.sha256)).hexdigest()
    )
    assert manifest.total_bytes == 3


@given(st.binary(max_size=100))
def test_order_invariance_and_byte_path_sensitivity(content: bytes) -> None:
    a, b = observation("a", content), observation("b", b"fixed")
    first = manifest_from_entries((a, b))
    assert first == manifest_from_entries((b, a))
    assert first != manifest_from_entries((observation("a", content + b"\0"), b))
    assert first != manifest_from_entries((observation("renamed", content), b))


@pytest.mark.parametrize(
    "bad", [FileObservation("a", 0, "bogus"), FileObservation("a", -1, "0" * 64)]
)
def test_invalid_entries(bad: FileObservation) -> None:
    with pytest.raises(InvalidInput):
        manifest_from_entries((bad,))


def test_case_collisions_rejected_without_filesystem_assumptions() -> None:
    with pytest.raises(InvalidInput):
        manifest_from_entries((observation("A", b""), observation("a", b"")))


@pytest.mark.parametrize("change", ["bytes", "add", "delete", "rename", "symlink"])
def test_source_drift(tmp_path: Path, change: str) -> None:
    source = tmp_path / "input"
    source.mkdir()
    data = source / "data"
    data.write_bytes(b"original")
    valid = InputGate().validate(source, tmp_path / "out", ScanLimits())
    inventory = InventoryService()
    with Snapshotter(tmp_path).create(valid) as snapshot:
        manifest = inventory.collect(snapshot)
        assert inventory.verify_unchanged(valid, manifest)
        if change == "bytes":
            data.write_bytes(b"modified")
        elif change == "add":
            (source / "extra").write_bytes(b"new")
        elif change == "delete":
            data.unlink()
        elif change == "rename":
            data.rename(source / "renamed")
        else:
            data.unlink()
            data.symlink_to(tmp_path / "out")
        assert not inventory.verify_unchanged(valid, manifest)
        assert inventory.verify_snapshot(snapshot, manifest)


def test_snapshot_drift_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "input"
    source.mkdir()
    (source / "data").write_bytes(b"original")
    valid = InputGate().validate(source, tmp_path / "out", ScanLimits())
    inventory = InventoryService()
    with Snapshotter(tmp_path).create(valid) as snapshot:
        manifest = inventory.collect(snapshot)
        (snapshot.root / "data").chmod(0o600)
        (snapshot.root / "data").write_bytes(b"changed")
        assert not inventory.verify_snapshot(snapshot, manifest)
        with pytest.raises(SnapshotChanged):
            inventory.collect(snapshot)
