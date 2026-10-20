"""Install actual built distributions with locked cached runtime dependencies."""

import json
import os
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


def command(arguments, cwd=ROOT, timeout=60):
    environment = {
        **os.environ,
        "UV_OFFLINE": "1",
        "UV_PYTHON_DOWNLOADS": "never",
        "NO_COLOR": "1",
        "CI": "1",
    }
    result = subprocess.run(
        arguments, cwd=cwd, env=environment, capture_output=True, text=True, timeout=timeout
    )
    assert result.returncode == 0, result.stderr
    return result


@pytest.fixture(scope="module")
def installed_candidate(tmp_path_factory):
    parent = tmp_path_factory.mktemp("release-candidate").resolve()
    dist = parent / "dist"
    command(["uv", "build", "--offline", "--out-dir", str(dist)])
    wheel = next(dist.glob("*.whl"))
    archive = next(dist.glob("*.tar.gz"))
    command(
        [
            "uv",
            "export",
            "--locked",
            "--no-dev",
            "--no-emit-project",
            "--format",
            "requirements-txt",
            "--output-file",
            str(parent / "runtime.txt"),
        ]
    )
    command(["uv", "venv", "--python", sys.executable, str(parent / "venv")])
    python = parent / "venv/bin/python"
    command(
        [
            "uv",
            "pip",
            "sync",
            "--offline",
            "--python",
            str(python),
            "--require-hashes",
            "--only-binary",
            ":all:",
            str(parent / "runtime.txt"),
        ]
    )
    command(["uv", "pip", "install", "--offline", "--python", str(python), "--no-deps", str(wheel)])
    command(["uv", "pip", "check", "--python", str(python)])
    return parent, python, wheel, archive


def invoke_installed(candidate, *args, network_guard=False):
    parent, python, _, _ = candidate
    entry = [str(python), "-I", "-m", "modelvet"]
    if network_guard:
        script = """
import socket
def denied(*args, **kwargs): raise AssertionError("Runtime networking attempted")
socket.socket.connect = denied
socket.socket.connect_ex = denied
socket.create_connection = denied
from modelvet.cli.main import app
app()
"""
        entry = [str(python), "-I", "-c", script]
    return subprocess.run([*entry, *args], cwd=parent, capture_output=True, text=True, timeout=15)


def test_candidate_archive_contents_and_installed_resources(installed_candidate) -> None:
    parent, python, wheel, archive = installed_candidate
    with zipfile.ZipFile(wheel) as package:
        names = package.namelist()
        assert any(name.endswith(".dist-info/licenses/LICENSE") for name in names)
        for source in (ROOT / "schemas").glob("*.json"):
            assert package.read("modelvet/schemas/" + source.name) == source.read_bytes()
        assert (
            package.read("modelvet/policies/default.toml")
            == (ROOT / "src/modelvet/policies/default.toml").read_bytes()
        )
    with tarfile.open(archive) as package:
        names = package.getnames()
        for suffix in (
            "examples/create_fixture.py",
            "examples/default.toml",
            "docs/POLICY_SPEC.md",
            ".github/workflows/ci.yml",
            "uv.lock",
        ):
            assert any(name.endswith("/" + suffix) for name in names), suffix
        assert not any("/docs/verification/" in name or "/.venv/" in name for name in names)
    result = command(
        [
            str(python),
            "-I",
            "-c",
            "import modelvet; from modelvet.core.config import load_policy; "
            "print(modelvet.__file__); print(load_policy().policy_id)",
        ],
        cwd=parent,
    )
    assert str(parent / "venv") in result.stdout and str(ROOT / "src") not in result.stdout
    assert "default-policy-v1" in result.stdout


def test_installed_commands_are_available(installed_candidate) -> None:
    for args in (
        ["--help"],
        ["version", "--json"],
        ["doctor", "--json"],
        ["policy", "validate", str(ROOT / "examples/default.toml"), "--json"],
    ):
        result = invoke_installed(installed_candidate, *args)
        assert result.returncode == 0, result.stderr
    assert json.loads(invoke_installed(installed_candidate, "version", "--json").stdout)[
        "schema_versions"
    ] == ["1.0.0"]


@pytest.mark.parametrize(
    "variant,expected", [("clean", 0), ("source", 20), ("malformed", 30), ("serialized", 30)]
)
def test_installed_candidate_scan_and_inspect_without_network(
    installed_candidate, variant, expected
) -> None:
    parent, python, _, _ = installed_candidate
    target = parent / variant
    command(
        [str(python), str(ROOT / "examples/create_fixture.py"), str(target), "--variant", variant],
        cwd=parent,
    )
    result = invoke_installed(
        installed_candidate,
        "scan",
        str(target),
        "--out",
        str(parent / "reports"),
        "--scanner",
        "none",
        "--json-summary",
        network_guard=True,
    )
    assert result.returncode == expected, result.stderr
    summary = json.loads(result.stdout)
    assert summary["exit_code"] == expected
    path = parent / "reports" / summary["report"]
    assert path.exists() and path.with_suffix(".md").exists()
    inspected = invoke_installed(installed_candidate, "inspect", str(path), "--format", "json")
    assert inspected.returncode == 0, inspected.stderr
    assert json.loads(inspected.stdout)["semantic_digest"] == summary["semantic_digest"]


def test_installed_controls_and_invalid_schema(installed_candidate) -> None:
    parent, python, _, _ = installed_candidate
    target = parent / "controls-input"
    command([str(python), str(ROOT / "examples/create_fixture.py"), str(target)], cwd=parent)
    result = invoke_installed(
        installed_candidate,
        "scan",
        str(target),
        "--out",
        str(parent / "controls-reports"),
        "--policy",
        str(ROOT / "examples/controls.toml"),
        "--json-summary",
        network_guard=True,
    )
    assert result.returncode == 10, result.stderr
    assert json.loads(result.stdout)["decision"] == "CONTROLS"
    broken = parent / "broken.json"
    broken.write_text('{"schema_version":"99.0.0"}')
    result = invoke_installed(installed_candidate, "inspect", str(broken), "--format", "json")
    assert result.returncode == 40 and result.stdout == ""


def test_installed_advisory_supplement_offline(installed_candidate) -> None:
    parent, python, _, _ = installed_candidate
    target = parent / "advisory-input"
    command([str(python), str(ROOT / "examples/create_fixture.py"), str(target)], cwd=parent)
    (target / "modelvet-environment.json").write_bytes(
        (ROOT / "examples/advisory-environment.json").read_bytes()
    )
    scan = invoke_installed(
        installed_candidate,
        "scan",
        str(target),
        "--out",
        str(parent / "advisory-reports"),
        "--json-summary",
        network_guard=True,
    )
    assert scan.returncode == 0, scan.stderr
    report = parent / "advisory-reports" / json.loads(scan.stdout)["report"]
    original = report.read_bytes()
    result = invoke_installed(
        installed_candidate,
        "advisories",
        str(report),
        "--as-of",
        "2026-10-20T12:00:00Z",
        "--snapshot",
        str(ROOT / "examples/advisory-snapshot.json"),
        network_guard=True,
    )
    assert result.returncode == 30, result.stderr
    output = json.loads(result.stdout)
    assert output["assessment"]["dependencies"][0]["result"] == "AFFECTED_VERSION"
    assert output["assessment"]["admission_recomputed"] is False
    assert report.read_bytes() == original
