import io
import json
import struct
import zipfile
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from modelvet.core.errors import InvalidInput
from modelvet.core.json_data import strict_json
from modelvet.core.limits import ScanLimits
from modelvet.core.snapshot import Snapshotter
from modelvet.inventory.classify import FileClassification, FileFormat
from modelvet.inventory.gate import InputGate
from modelvet.inventory.identity import InventoryService
from modelvet.structural.safetensors import SafetensorsInspector
from modelvet.structural.zip_index import ZipIndexInspector


def safetensor(header: dict[str, object], data: bytes = b"") -> bytes:
    raw = json.dumps(header).encode()
    return len(raw).to_bytes(8, "little") + raw + data


def inspect_bytes(tmp_path: Path, name: str, raw: bytes, limits: ScanLimits | None = None):
    source = tmp_path / "input"
    source.mkdir()
    (source / name).write_bytes(raw)
    valid = InputGate().validate(source, tmp_path / "out", limits or ScanLimits())
    with Snapshotter(tmp_path).create(valid) as snapshot:
        (file,) = InventoryService().collect(snapshot).files
        inspector = SafetensorsInspector() if name.endswith("safetensors") else ZipIndexInspector()
        return inspector.inspect(file, snapshot)


def test_safetensors_valid_and_metadata_only(tmp_path: Path) -> None:
    raw = safetensor(
        {
            "weight": {"dtype": "F32", "shape": [1], "data_offsets": [0, 4]},
            "__metadata__": {"license": "declared-only"},
        },
        b"\0" * 4,
    )
    result = inspect_bytes(tmp_path, "model.safetensors", raw)
    assert result.status == "COMPLETE"
    assert result.details == {"tensor_count": 1}


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"bad",
        b"\xff" * 8,
        b'\x0d\0\0\0\0\0\0\0{"a":1,"a":2}',
        safetensor({"t": {"dtype": "F32", "shape": [1], "data_offsets": [0, 8]}}, b"\0" * 8),
        safetensor({"t": {"dtype": "U8", "shape": [1], "data_offsets": [1, 2]}}, b"\0" * 2),
        safetensor({"t": {"dtype": "U8", "shape": [True], "data_offsets": [0, 1]}}, b"\0"),
        safetensor({"__metadata__": {"bad": 1}}),
    ],
)
def test_safetensors_malformed(tmp_path: Path, raw: bytes) -> None:
    assert inspect_bytes(tmp_path, "model.safetensors", raw).status == "FAILED"


def test_safetensors_unsupported_dtype(tmp_path: Path) -> None:
    raw = safetensor({"t": {"dtype": "F4", "shape": [2], "data_offsets": [0, 1]}}, b"\0")
    assert inspect_bytes(tmp_path, "model.safetensors", raw).status == "UNSUPPORTED"


def zip_bytes(names: list[str], compression: int = zipfile.ZIP_STORED) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=compression) as archive:
        for name in names:
            archive.writestr(name, b"inert content")
    return output.getvalue()


@pytest.mark.parametrize("method", [zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED])
def test_zip_valid_index_without_extraction(
    tmp_path: Path, method: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = zip_bytes(["archive/data", "archive/config"], method)

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("No extraction permitted")

    monkeypatch.setattr(zipfile.ZipFile, "extractall", forbidden)
    result = inspect_bytes(tmp_path, "model.zip", raw)
    assert result.status == "COMPLETE"
    assert len(result.details["members"]) == 2


@pytest.mark.parametrize("name", ["../escape", "/absolute", "C:/drive", "a\\b", "a\nb"])
def test_zip_unsafe_member_paths(tmp_path: Path, name: str) -> None:
    assert inspect_bytes(tmp_path, "model.zip", zip_bytes([name])).status == "FAILED"


def test_zip_header_disagreement(tmp_path: Path) -> None:
    raw = bytearray(zip_bytes(["first"]))
    raw[30:35] = b"other"
    assert inspect_bytes(tmp_path, "model.zip", bytes(raw)).status == "FAILED"


def test_zip_index_count_disagreement(tmp_path: Path) -> None:
    raw = bytearray(zip_bytes(["first"]))
    at = raw.rfind(b"PK\x05\x06")
    struct.pack_into("<HH", raw, at + 8, 0, 0)
    assert inspect_bytes(tmp_path, "model.zip", bytes(raw)).status == "FAILED"


def test_zip_metadata_budget(tmp_path: Path) -> None:
    assert (
        inspect_bytes(
            tmp_path, "model.zip", zip_bytes(["a"]), ScanLimits(max_metadata_bytes=32)
        ).status
        == "FAILED"
    )


@pytest.mark.parametrize(
    "raw", [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e999}', b'"\\ud800"', b"[" * 65 + b"]" * 65]
)
def test_json_ambiguity_nonfinite_depth_rejected(raw: bytes) -> None:
    with pytest.raises(InvalidInput):
        strict_json(raw, 1024)


@given(st.binary(max_size=256))
def test_json_parser_fails_in_controlled_way(raw: bytes) -> None:
    try:
        strict_json(raw, 256)
    except InvalidInput:
        pass


def test_zip_duplicate_members(tmp_path: Path) -> None:
    with pytest.warns(UserWarning, match="Duplicate name"):
        raw = zip_bytes(["same", "same"])
    assert inspect_bytes(tmp_path, "model.zip", raw).status == "FAILED"


def test_zip_special_member_type(tmp_path: Path) -> None:
    raw = bytearray(zip_bytes(["link"]))
    at = raw.index(b"PK\x01\x02")
    struct.pack_into("<I", raw, at + 38, 0o120777 << 16)
    assert inspect_bytes(tmp_path, "model.zip", bytes(raw)).status == "FAILED"


@pytest.mark.parametrize("flags", [1, 8, 64])
def test_zip_unsupported_features(tmp_path: Path, flags: int) -> None:
    raw = bytearray(zip_bytes(["data"]))
    at = raw.index(b"PK\x01\x02")
    struct.pack_into("<H", raw, at + 8, flags)
    assert inspect_bytes(tmp_path, "model.zip", bytes(raw)).status == "UNSUPPORTED"


def test_safetensors_overlap_rejected(tmp_path: Path) -> None:
    tensor = {"dtype": "U8", "shape": [1], "data_offsets": [0, 1]}
    raw = safetensor({"first": tensor, "second": tensor}, b"a")
    assert inspect_bytes(tmp_path, "model.safetensors", raw).status == "FAILED"


def test_inspector_applicability_is_scoped() -> None:
    for kind in FileFormat:
        classification = FileClassification(kind, ())
        assert SafetensorsInspector().applies_to(classification) == (kind == FileFormat.SAFETENSORS)
        assert ZipIndexInspector().applies_to(classification) == (
            kind in {FileFormat.PYTORCH_ZIP, FileFormat.ZIP_OTHER}
        )
