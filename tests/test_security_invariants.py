import ast
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from fixture_factory import artifact

from modelvet.core.errors import InvalidInput
from modelvet.core.limits import ScanLimits
from modelvet.core.snapshot import Snapshotter
from modelvet.inventory.gate import InputGate, has_ancestor_identity, open_directory
from modelvet.scanners.process import run_bounded, safe_environment

ROOT = Path(__file__).parents[1]


def forbidden_calls(text):
    names = set()
    forbidden = {
        "eval",
        "exec",
        "__import__",
        "pickle.load",
        "pickle.loads",
        "torch.load",
        "dill.load",
        "joblib.load",
        "marshal.load",
        "importlib.import_module",
    }
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Call):
            name = ast.unparse(node.func)
            if name in forbidden or name.endswith(".from_pretrained"):
                names.add(name)
    return names


def test_static_no_host_loaders_or_dynamic_artifact_imports() -> None:
    for source in (ROOT / "src/modelvet").rglob("*.py"):
        assert not forbidden_calls(source.read_text()), source
        if source.parent.name in {"core", "evidence"}:
            for node in ast.walk(ast.parse(source.read_text())):
                if isinstance(node, ast.ImportFrom):
                    assert not (node.module or "").startswith(("modelvet.cli", "modelvet.reports"))
    assert forbidden_calls("torch.load(path); eval(data); obj.from_pretrained(path)")
    assert not forbidden_calls("json.loads(data)")


def test_only_reviewed_process_boundary_can_launch_children() -> None:
    launches = []
    for source in (ROOT / "src/modelvet").rglob("*.py"):
        for node in ast.walk(ast.parse(source.read_text())):
            if isinstance(node, ast.Call) and ast.unparse(node.func) in {
                "subprocess.Popen",
                "subprocess.run",
                "os.system",
                "os.popen",
            }:
                launches.append(source)
                assert ast.unparse(node.func) == "subprocess.Popen"
                keywords = {k.arg: k.value for k in node.keywords}
                assert ast.literal_eval(keywords["shell"]) is False
                assert ast.literal_eval(keywords["close_fds"]) is True
                assert ast.literal_eval(keywords["start_new_session"]) is True
    assert launches == [ROOT / "src/modelvet/scanners/process.py"]


def test_environment_excludes_ambient_secrets(tmp_path, monkeypatch) -> None:
    for key in ("AWS_SECRET_ACCESS_KEY", "PYTHONPATH", "HTTP_PROXY", "MODELVET_POLICY"):
        monkeypatch.setenv(key, "sentinel-secret")
    environment = safe_environment(tmp_path)
    assert "sentinel-secret" not in str(environment)
    assert set(environment) == {
        "PATH",
        "HOME",
        "TMPDIR",
        "LC_ALL",
        "PYTHONNOUSERSITE",
        "PYTHONDONTWRITEBYTECODE",
        "OPENBLAS_NUM_THREADS",
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
    }


def test_directory_ancestry_uses_identity_not_spelling(tmp_path) -> None:
    root = artifact(tmp_path / "Artifact")
    (root / "child").mkdir()
    descriptor = open_directory(root / "child")
    try:
        info = os.stat(root)
        assert has_ancestor_identity(descriptor, info.st_dev, info.st_ino)
        assert not has_ancestor_identity(descriptor, info.st_dev, info.st_ino + 100000)
    finally:
        os.close(descriptor)
    alias = tmp_path / "artifact"
    if alias.exists() and alias.samefile(root):
        with pytest.raises(InvalidInput):
            InputGate().validate(root, alias / "reports", ScanLimits())
        source = InputGate().validate(root, tmp_path / "reports", ScanLimits())
        with pytest.raises(InvalidInput), Snapshotter(alias).create(source):
            pass
        assert not list(root.glob("modelvet-snapshot-*"))


def test_normal_exit_cleans_process_group_descendants(tmp_path) -> None:
    body = (
        "import subprocess,sys; "
        "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],"
        "stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); print(child.pid,flush=True)"
    )
    result = run_bounded((sys.executable, "-c", body), tmp_path, 3)
    assert result.exit_code == 0
    pid = int(result.stdout.strip())
    for _ in range(20):
        state = subprocess.run(
            ["/bin/ps", "-o", "state=", "-p", str(pid)], capture_output=True, text=True, timeout=2
        ).stdout.strip()
        if not state or state.startswith("Z"):
            break
        time.sleep(0.05)
    assert not state or state.startswith("Z")


def test_report_requires_versioned_complete_producers() -> None:
    import json

    from test_reports import make_report

    from modelvet.reports.json_report import parse_report, semantic_digest

    data = make_report().model_dump(mode="json")
    data["tools"] = []
    data["semantic_digest"] = semantic_digest(data)
    with pytest.raises(InvalidInput):
        parse_report(json.dumps(data).encode())


def test_unknown_scanner_exit_cannot_be_normalized_complete() -> None:
    from dataclasses import replace

    from test_evidence import fixture

    from modelvet.evidence.normalize import EvidenceNormalizer

    manifest, raw, classes = fixture(scanned=["weights.pkl"])
    _, checks, _ = EvidenceNormalizer().normalize(manifest, replace(raw, exit_code=99), classes)
    assert all(c.status != "COMPLETE" for c in checks if c.check_id == "modelscan")


@pytest.mark.parametrize(
    "declaration", [{"trust_remote_code": True}, {"auto_map": {"AutoModel": "custom.Model"}}]
)
def test_declared_remote_loader_is_unresolved_not_clean(tmp_path, declaration) -> None:
    import json

    from test_cli import invoke

    root = artifact(tmp_path / "model")
    target = root / "config.json"
    target.write_text(json.dumps({**json.loads(target.read_text()), **declaration}))
    result = invoke("scan", str(root), "--out", str(tmp_path / "out"), "--json-summary")
    assert result.returncode == 30, result.stderr
    assert "UNRESOLVED-FINDING" in json.loads(result.stdout)["rule_ids"]
