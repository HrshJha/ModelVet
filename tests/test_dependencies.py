import json
from pathlib import Path

import pytest

from modelvet.core.limits import ScanLimits
from modelvet.core.snapshot import Snapshotter
from modelvet.dependencies.manifest import MANIFEST_NAME, DependencyReader
from modelvet.inventory.gate import InputGate
from modelvet.inventory.identity import InventoryService


def assess(tmp_path: Path, raw: bytes | None):
    source = tmp_path / "input"
    source.mkdir()
    if raw is not None:
        (source / MANIFEST_NAME).write_bytes(raw)
    valid = InputGate().validate(source, tmp_path / "out", ScanLimits())
    with Snapshotter(tmp_path).create(valid) as snapshot:
        return DependencyReader().assess(snapshot, InventoryService().collect(snapshot))


def envelope(rows: list[dict[str, object]]) -> bytes:
    return json.dumps({"schema_version": "1.0.0", "dependencies": rows}).encode()


def test_explicit_pins_are_claims_with_sources(tmp_path: Path) -> None:
    result = assess(
        tmp_path, envelope([{"name": "Torch_CPU", "ecosystem": "PyPI", "version": "2.6.0+cpu"}])
    )
    assert result.check.status == "COMPLETE"
    (record,) = result.records
    assert (record.name, record.version, record.status) == (
        "torch-cpu",
        "2.6.0+cpu",
        "DECLARED_PINNED",
    )
    assert record.source_ref.endswith("#json:/dependencies/0")
    assert len(record.source_sha256) == 64
    assert "unverified" in result.check.limitations[0]


def test_absent_manifest_is_explicit(tmp_path: Path) -> None:
    result = assess(tmp_path, None)
    assert result.records == () and result.file_id is None
    assert result.check.status == "UNSUPPORTED"


@pytest.mark.parametrize("version", [None, "latest", ">=2", "2.*", "2.0; marker", ""])
def test_unpinned_versions_inconclusive(tmp_path: Path, version: object) -> None:
    result = assess(
        tmp_path, envelope([{"name": "torch", "ecosystem": "PyPI", "version": version}])
    )
    assert result.records[0].status == "INCONCLUSIVE"
    assert result.check.status == "UNSUPPORTED"


def test_conflicting_pins_preserved(tmp_path: Path) -> None:
    result = assess(
        tmp_path,
        envelope(
            [
                {"name": "Torch_CPU", "ecosystem": "PyPI", "version": "2.0"},
                {"name": "torch-cpu", "ecosystem": "PyPI", "version": "3.0"},
            ]
        ),
    )
    assert {record.version for record in result.records} == {"2.0", "3.0"}
    assert all(record.status == "INCONCLUSIVE" for record in result.records)


@pytest.mark.parametrize(
    "raw",
    [
        b"not JSON",
        b'{"schema_version":"1.0.0","dependencies":{},"unknown":1}',
        b'{"schema_version":"1.0.0","dependencies":[],"dependencies":[]}',
        envelope([{"name": "bad/name", "ecosystem": "PyPI"}]),
    ],
)
def test_malformed_manifests_fail(tmp_path: Path, raw: bytes) -> None:
    assert assess(tmp_path, raw).check.status == "FAILED"


def test_unsupported_schema(tmp_path: Path) -> None:
    assert (
        assess(tmp_path, b'{"schema_version":"2.0.0","dependencies":[]}').check.status
        == "UNSUPPORTED"
    )


def test_unsupported_ecosystem_not_verified(tmp_path: Path) -> None:
    result = assess(tmp_path, envelope([{"name": "torch", "ecosystem": "Other", "version": "1.0"}]))
    assert result.records[0].status == "INCONCLUSIVE"
