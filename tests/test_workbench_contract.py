"""FR-025–027 contracts and optional dependency boundary."""

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


def test_workbench_traceability() -> None:
    prd = (ROOT / "PRD.md").read_text()
    tasks = (ROOT / "docs/TASKS.md").read_text()
    roadmap = (ROOT / "docs/ROADMAP.md").read_text()
    assert all(f"| FR-{i:03d} |" in prd for i in range(25, 28))
    assert re.findall(r"^### (MV-\d{3}) —", tasks, re.M) == [f"MV-{i:03d}" for i in range(1, 46)]
    assert "PH-15" in roadmap and "PH-17" in roadmap


def test_ui_dependencies_are_optional_and_pinned() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
    assert project["dependencies"] == ["typer==0.27.3", "pydantic==2.14.1"]
    assert all("==" in dep for dep in project["optional-dependencies"]["ui"])
    assert {dep.split("==")[0] for dep in project["optional-dependencies"]["ui"]} == {
        "fastapi",
        "uvicorn",
    }


def test_frontend_manifest_and_lock_agree() -> None:
    package = json.loads((ROOT / "frontend/package.json").read_text())
    lock = json.loads((ROOT / "frontend/package-lock.json").read_text())
    for section in ("dependencies", "devDependencies"):
        for name, version in package[section].items():
            assert version == lock["packages"][f"node_modules/{name}"]["version"]
            assert lock["packages"][f"node_modules/{name}"]["integrity"].startswith("sha512-")


def test_core_cli_import_does_not_require_ui_extra() -> None:
    script = """
import sys
sys.modules['fastapi'] = None
sys.modules['uvicorn'] = None
from modelvet.cli.main import app
assert app is not None
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", script], capture_output=True, text=True, timeout=15
    )
    assert result.returncode == 0, result.stderr


def test_optional_python_stack_smoke() -> None:
    pytest.importorskip("fastapi")
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()

    @app.get("/probe")
    def probe() -> dict[str, str]:
        return {"status": "combined-stack-ok"}

    with TestClient(app) as client:
        assert client.get("/probe").json() == {"status": "combined-stack-ok"}
