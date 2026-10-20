from pathlib import Path

import pytest

from modelvet.core.limits import ScanLimits
from modelvet.core.snapshot import Snapshotter
from modelvet.inventory.gate import InputGate
from modelvet.inventory.identity import InventoryService
from modelvet.metadata.claims import MetadataReader


def assess(tmp_path: Path, files: dict[str, bytes], limits: ScanLimits | None = None):
    source = tmp_path / "input"
    source.mkdir()
    for name, content in files.items():
        (source / name).write_bytes(content)
    valid = InputGate().validate(source, tmp_path / "out", limits or ScanLimits())
    with Snapshotter(tmp_path).create(valid) as snapshot:
        return MetadataReader().assess(snapshot, InventoryService().collect(snapshot))


def test_opposing_claims_preserve_sources(tmp_path: Path) -> None:
    result = assess(
        tmp_path,
        {
            "README.md": b"---\nlicense: Apache-2.0\n---\n",
            "config.json": b'{"license":"CC-BY-NC","revision":"abc123"}',
        },
    )
    licenses = [claim for claim in result.claims if claim.kind == "LICENSE"]
    assert {claim.value for claim in licenses} == {"Apache-2.0", "CC-BY-NC"}
    assert len({claim.source_file_id for claim in licenses}) == 2
    assert next(claim for claim in licenses if claim.value == "CC-BY-NC").source_ref.endswith(
        "#json:/license"
    )
    assert all(
        len(claim.source_sha256) == 64 and claim.confidence == "DECLARED" for claim in licenses
    )
    assert next(claim for claim in licenses if claim.value == "Apache-2.0").source_line == 2
    assert result.missing_kinds == ()


def test_missing_claims_explicit(tmp_path: Path) -> None:
    result = assess(tmp_path, {"config.json": b"{}"})
    assert result.claims == ()
    assert set(result.missing_kinds) == {"LICENSE", "PROVENANCE"}
    assert all(check.status == "COMPLETE" for check in result.checks.values())


@pytest.mark.parametrize("raw", [b'{"license":"MIT","license":"other"}', b"\xff", b"[]"])
def test_invalid_json_metadata(tmp_path: Path, raw: bytes) -> None:
    result = assess(tmp_path, {"config.json": raw})
    assert next(iter(result.checks.values())).status == "FAILED"


@pytest.mark.parametrize(
    "name,raw",
    [
        ("config.json", b'{"license":{"name":"ambiguous"}}'),
        ("README.md", b"---\nlicense: |\n  multiline\n---"),
        ("README.md", b"---\nlicense: MIT"),
    ],
)
def test_unsupported_claims(tmp_path: Path, name: str, raw: bytes) -> None:
    result = assess(tmp_path, {name: raw})
    assert next(iter(result.checks.values())).status == "UNSUPPORTED"


def test_spdx_and_license_document_title(tmp_path: Path) -> None:
    result = assess(
        tmp_path,
        {
            "LICENSE": b"MIT License\nlocal declaration",
            "NOTICE": b"SPDX-License-Identifier: Apache-2.0",
        },
    )
    assert {claim.value for claim in result.claims} == {"MIT License", "Apache-2.0"}
    assert any("text-title" in claim.source_ref for claim in result.claims)


def test_remote_code_flags_are_only_claims(tmp_path: Path) -> None:
    result = assess(
        tmp_path,
        {
            "config.json": b'{"trust_remote_code":true,"auto_map":{"AutoModel":"modeling.Foo"}}',
            "modeling.py": b"raise RuntimeError('must never import')",
        },
    )
    assert {claim.value for claim in result.claims} == {
        "trust_remote_code=true",
        "custom_loader_mapping_declared",
    }
    assert all(claim.confidence == "DECLARED" for claim in result.claims)


def test_oversized_metadata_is_not_truncated_to_success(tmp_path: Path) -> None:
    result = assess(tmp_path, {"README.md": b"a" * 64}, ScanLimits(max_metadata_bytes=32))
    assert next(iter(result.checks.values())).status == "UNSUPPORTED"
