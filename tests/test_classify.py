from pathlib import Path

import pytest

from modelvet.core.errors import InvalidInput
from modelvet.core.limits import ScanLimits
from modelvet.core.snapshot import Snapshotter
from modelvet.inventory.classify import Classifier, FileFormat
from modelvet.inventory.gate import InputGate
from modelvet.inventory.identity import InventoryService


@pytest.mark.parametrize(
    "name,content,kind,mismatch",
    [
        ("weights.safetensors", b"\x02\0\0\0\0\0\0\0{}", FileFormat.SAFETENSORS, False),
        ("weights.safetensors", b"broken", FileFormat.SAFETENSORS, True),
        ("weights.pt", b"PK\x03\x04inert", FileFormat.PYTORCH_ZIP, False),
        ("weights.pkl", b"\x80\x04inert", FileFormat.PICKLE_LIKE, False),
        ("archive.zip", b"PK\x05\x06inert", FileFormat.ZIP_OTHER, False),
        ("config.json", b"PK\x03\x04inert", FileFormat.ZIP_OTHER, True),
        ("config.json", b"{}", FileFormat.JSON, False),
        ("README.md", b"# Model", FileFormat.MARKDOWN, False),
        ("LICENSE", b"local claim", FileFormat.TEXT, False),
        ("modeling.py", b"raise RuntimeError('must never run')", FileFormat.PYTHON_SOURCE, False),
        ("unknown.bin", b"\0opaque", FileFormat.BINARY_UNKNOWN, False),
        ("unknown.data", b"unclassified text", FileFormat.UNKNOWN, False),
    ],
)
def test_classification(
    tmp_path: Path, name: str, content: bytes, kind: FileFormat, mismatch: bool
) -> None:
    source = tmp_path / "input"
    source.mkdir()
    (source / name).write_bytes(content)
    valid = InputGate().validate(source, tmp_path / "out", ScanLimits())
    with Snapshotter(tmp_path).create(valid) as snapshot:
        (file,) = InventoryService().collect(snapshot).files
        result = Classifier().classify(file, snapshot)
        assert result.format_class == kind
        assert result.mismatch == mismatch
        assert {"identity", "classification"} <= set(result.check_ids)
        if kind in {FileFormat.UNKNOWN, FileFormat.BINARY_UNKNOWN}:
            assert result.reason == "Unsupported security-relevant format."
        if kind in {FileFormat.PICKLE_LIKE, FileFormat.PYTORCH_ZIP}:
            assert "modelscan" in result.check_ids


@pytest.mark.parametrize("replace", ["missing", "symlink"])
def test_changed_snapshot_paths_fail_closed(tmp_path: Path, replace: str) -> None:
    source = tmp_path / "input"
    source.mkdir()
    (source / "data.json").write_bytes(b"{}")
    valid = InputGate().validate(source, tmp_path / "out", ScanLimits())
    with Snapshotter(tmp_path).create(valid) as snapshot:
        (file,) = InventoryService().collect(snapshot).files
        target = snapshot.root / file.relpath
        target.unlink()
        if replace == "symlink":
            target.symlink_to(source / "data.json")
        with pytest.raises(InvalidInput):
            Classifier().classify(file, snapshot)
