"""Packaging checks independent of the future scanner and artifact pipeline."""

import json
import subprocess
import sys
from importlib.metadata import distribution

from packaging.specifiers import SpecifierSet

import modelvet


def test_installed_metadata_matches_package() -> None:
    package = distribution("modelvet")
    assert package.version == modelvet.__version__
    assert set(package.metadata["Requires-Python"].split(",")) == {">=3.12", "<3.13"}
    assert package.metadata["License-Expression"] == "MIT"
    requirements = package.requires or []
    assert {requirement.split("==", 1)[0] for requirement in requirements} == {
        "pydantic",
        "typer",
    }


def test_python_support_metadata_excludes_unsupported_versions() -> None:
    supported = SpecifierSet(distribution("modelvet").metadata["Requires-Python"])
    assert "3.12.0" in supported
    assert "3.12.15" in supported
    assert all(version not in supported for version in ("3.11.9", "3.13.0", "3.14.3"))


def test_isolated_import_does_not_load_model_runtime() -> None:
    script = """
import json
import sys
import modelvet
forbidden = {'torch', 'transformers', 'modelscan', 'pickle', 'dill', 'joblib'}
print(json.dumps({
    'version': modelvet.__version__,
    'loaded': sorted(forbidden & sys.modules.keys()),
}))
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", script],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert json.loads(result.stdout) == {"version": modelvet.__version__, "loaded": []}
    assert result.stderr == ""
