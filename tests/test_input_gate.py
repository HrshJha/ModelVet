import os
from pathlib import Path

import pytest

from modelvet.core.errors import InvalidInput
from modelvet.core.limits import ScanLimits
from modelvet.inventory.gate import InputGate


def test_valid_input_does_not_create_output(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    output = tmp_path / "new" / "reports"
    result = InputGate().validate(artifact, output, ScanLimits())
    assert result.artifact_dir == artifact
    assert result.output_dir == output
    assert result.root_inode == artifact.stat().st_ino
    assert not output.exists()


@pytest.mark.parametrize("kind", ["missing", "file", "symlink", "symlink-parent", "traversal"])
def test_invalid_source_paths(tmp_path: Path, kind: str) -> None:
    artifact = tmp_path / "artifact"
    if kind == "file":
        artifact.write_text("not a directory")
    elif kind in {"symlink", "symlink-parent"}:
        actual = tmp_path / "actual"
        actual.mkdir()
        artifact.symlink_to(actual, target_is_directory=True)
        if kind == "symlink-parent":
            (actual / "child").mkdir()
            artifact /= "child"
    elif kind == "traversal":
        artifact = tmp_path / ".." / tmp_path.name
    with pytest.raises(InvalidInput):
        InputGate().validate(artifact, tmp_path / "out", ScanLimits())


@pytest.mark.parametrize("kind", ["inside", "same", "symlink", "file"])
def test_output_boundary(tmp_path: Path, kind: str) -> None:
    artifact = tmp_path / "artifact"
    artifact.mkdir()
    output = tmp_path / "out"
    if kind == "same":
        output = artifact
    elif kind == "inside":
        output = artifact / "reports"
    elif kind == "symlink":
        output.symlink_to(artifact, target_is_directory=True)
    else:
        output.write_text("preserve")
    with pytest.raises(InvalidInput):
        InputGate().validate(artifact, output, ScanLimits())


@pytest.mark.parametrize("value", [0, -1, 10_001, True])
def test_limits_cannot_bypass_ceilings(value: int) -> None:
    with pytest.raises(InvalidInput):
        ScanLimits(max_files=value)


@pytest.mark.skipif(os.geteuid() == 0, reason="Root bypasses permission checks")
def test_unreadable_input(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact"
    artifact.mkdir(mode=0o000)
    try:
        with pytest.raises(InvalidInput):
            InputGate().validate(artifact, tmp_path / "out", ScanLimits())
    finally:
        artifact.chmod(0o700)
