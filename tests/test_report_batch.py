import hashlib
import json
import os
from pathlib import Path

import pytest
from pydantic import ValidationError
from test_cli import invoke
from test_report_audit import saved

from modelvet.core.errors import InvalidInput
from modelvet.reports import batch
from modelvet.reports.batch import BatchAudit, BatchManifest, audit_batch


def manifest(tmp_path, paths, root=None, pins=None):
    root = root or tmp_path
    data = {
        "schema_version": "1.0.0",
        "reports": [
            {
                "path": str(path.relative_to(root)),
                **({"expected_report_sha256": pins[index]} if pins else {}),
            }
            for index, path in enumerate(paths)
        ],
    }
    target = tmp_path / "batch.json"
    target.write_text(json.dumps(data))
    return target


def pair(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    left, _ = saved(tmp_path / "a", (b"one",))
    right, _ = saved(tmp_path / "b", (b"two",))
    return left, right


def test_valid_batch_no_writes_no_paths_and_pins(tmp_path):
    paths = pair(tmp_path)
    pins = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
    target = manifest(tmp_path, paths, pins=pins)
    before = [path.read_bytes() for path in paths]
    result = audit_batch(target, tmp_path)
    assert result.status == "VERIFIED" and result.verified_reports == 2
    assert result.raw_bytes_read == 6
    assert result.report_bytes_charged == 2 * sum(len(raw) for raw in before)
    assert result.admission_recomputed is False
    assert str(tmp_path) not in result.model_dump_json()
    assert [path.read_bytes() for path in paths] == before
    assert BatchAudit.model_validate_json(result.model_dump_json()) == result


@pytest.mark.parametrize("failure", ["missing", "invalid", "raw-missing", "pin"])
def test_row_failure_keeps_later_report_and_blocks_aggregate(tmp_path, failure):
    paths = pair(tmp_path)
    pins = None
    if failure == "missing":
        paths[0].unlink()
    elif failure == "invalid":
        paths[0].write_text("password=DO_NOT_ECHO")
    elif failure == "raw-missing":
        for path in (paths[0].parent / "raw").iterdir():
            path.unlink()
    else:
        pins = ["f" * 64, hashlib.sha256(paths[1].read_bytes()).hexdigest()]
    target = manifest(tmp_path, paths, pins=pins)
    result = audit_batch(target, tmp_path)
    assert result.status == "INCOMPLETE"
    assert result.rows[1].status == "VERIFIED" and result.unresolved_reports == 1
    assert "DO_NOT_ECHO" not in result.model_dump_json()
    assert [r.index for r in result.rows] == [0, 1]


def test_report_and_raw_budget_accounting(tmp_path):
    paths = pair(tmp_path)
    target = manifest(tmp_path, paths)
    first = len(paths[0].read_bytes()) * 2
    result = audit_batch(target, tmp_path, max_report_bytes=first)
    assert [r.status for r in result.rows] == ["VERIFIED", "BUDGET_EXCEEDED"]
    assert result.report_bytes_charged == first
    result = audit_batch(target, tmp_path, max_raw_bytes=3)
    assert [r.status for r in result.rows] == ["VERIFIED", "BUDGET_EXCEEDED"]
    assert result.raw_bytes_read == 3 and result.status == "INCOMPLETE"
    result = audit_batch(target, tmp_path, max_report_bytes=0)
    assert all(r.status == "BUDGET_EXCEEDED" for r in result.rows)
    assert result.raw_bytes_read == result.report_bytes_charged == 0


@pytest.mark.parametrize(
    "entry",
    ["../escape.json", "/absolute.json", "a//report.json", "a\\report.json", "a/./report.json"],
)
def test_unsafe_manifest_paths(tmp_path, entry):
    target = tmp_path / "batch.json"
    target.write_text(json.dumps({"schema_version": "1.0.0", "reports": [{"path": entry}]}))
    with pytest.raises(InvalidInput):
        audit_batch(target, tmp_path)


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"schema_version": "2.0.0", "reports": []},
        {"schema_version": "1.0.0", "reports": []},
        {"schema_version": "1.0.0", "reports": [{"path": "a.json"}, {"path": "A.json"}]},
        {"schema_version": "1.0.0", "reports": [{"path": f"{i}.json"} for i in range(33)]},
        {
            "schema_version": "1.0.0",
            "reports": [{"path": "a.json", "expected_report_sha256": True}],
        },
        {"schema_version": "1.0.0", "reports": [{"path": "a.json"}], "scanner": "untrusted-code"},
    ],
)
def test_invalid_envelope(tmp_path, data):
    target = tmp_path / "batch.json"
    target.write_text(json.dumps(data))
    with pytest.raises(InvalidInput):
        audit_batch(target, tmp_path)


def test_manifest_and_report_links_are_rejected(tmp_path):
    paths = pair(tmp_path)
    target = manifest(tmp_path, paths)
    linked = tmp_path / "manifest-link"
    linked.symlink_to(target)
    with pytest.raises(InvalidInput):
        audit_batch(linked, tmp_path)
    (tmp_path / "root-link").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(InvalidInput):
        audit_batch(target, tmp_path / "root-link")
    raw = paths[0].read_bytes()
    paths[0].unlink()
    replacement = tmp_path / "other"
    replacement.write_bytes(raw)
    paths[0].symlink_to(replacement)
    result = audit_batch(target, tmp_path)
    assert result.rows[0].status == "INVALID" and result.rows[1].status == "VERIFIED"


def test_manifest_budget_and_duplicate_json_keys(tmp_path):
    path = tmp_path / "batch.json"
    path.write_bytes(b'{"schema_version":"1.0.0","reports":[],"reports":[]}')
    with pytest.raises(InvalidInput):
        audit_batch(path, tmp_path)
    path.write_bytes(b" " * (64 * 1024 + 1))
    with pytest.raises(InvalidInput):
        audit_batch(path, tmp_path)
    path.unlink()
    os.mkfifo(path)
    with pytest.raises(InvalidInput):
        audit_batch(path, tmp_path)


@pytest.mark.parametrize(
    "options",
    [
        {"max_report_bytes": True},
        {"max_report_bytes": -1},
        {"max_report_bytes": 129 * 1024 * 1024},
        {"max_raw_bytes": 129 * 1024 * 1024},
    ],
)
def test_budget_ceiling_validation(tmp_path, options):
    paths = pair(tmp_path)
    with pytest.raises(InvalidInput):
        audit_batch(manifest(tmp_path, paths), tmp_path, **options)


def test_changed_manifest_cannot_yield_verified(tmp_path, monkeypatch):
    paths = pair(tmp_path)
    target = manifest(tmp_path, paths)
    original = batch._manifest_bytes
    calls = 0

    def changed(path):
        nonlocal calls
        calls += 1
        return original(path) + (b" " if calls > 1 else b"")

    monkeypatch.setattr(batch, "_manifest_bytes", changed)
    result = audit_batch(target, tmp_path)
    assert result.verified_reports == 2
    assert result.status == "INCOMPLETE" and not result.manifest_unchanged


def test_changed_root_cannot_yield_verified(tmp_path, monkeypatch):
    root = tmp_path / "pool"
    root.mkdir()
    path, _ = saved(root)
    target = manifest(tmp_path, [path], root=root)
    original = batch._audit_captured

    def changed(*args, **kwargs):
        result = original(*args, **kwargs)
        root.rename(tmp_path / "moved")
        root.mkdir()
        return result

    monkeypatch.setattr(batch, "_audit_captured", changed)
    result = audit_batch(target, root)
    assert result.status == "INCOMPLETE" and not result.root_unchanged


def test_schemas_and_false_aggregate_tampering(tmp_path):
    root = Path(__file__).parents[1]
    for model, name in [
        (BatchAudit, "report-batch-audit-v1.json"),
        (BatchManifest, "report-batch-manifest-v1.json"),
    ]:
        assert model.model_json_schema() == json.loads((root / "schemas" / name).read_text())
    paths = pair(tmp_path)
    paths[0].unlink()
    result = audit_batch(manifest(tmp_path, paths), tmp_path)
    data = result.model_dump(mode="json")
    data["status"] = "VERIFIED"
    with pytest.raises(ValidationError):
        BatchAudit.model_validate_json(json.dumps(data))


def test_batch_cli_exit_classes_and_path_privacy(tmp_path):
    paths = pair(tmp_path)
    target = manifest(tmp_path, paths)
    result = invoke("audit-batch", str(target), "--root", str(tmp_path))
    assert result.returncode == 0 and json.loads(result.stdout)["verified_reports"] == 2
    assert str(tmp_path) not in result.stdout + result.stderr
    paths[0].unlink()
    result = invoke("audit-batch", str(target), "--root", str(tmp_path))
    assert result.returncode == 30 and json.loads(result.stdout)["unresolved_reports"] == 1
    target.write_text("invalid")
    result = invoke("audit-batch", str(target), "--root", str(tmp_path))
    assert result.returncode == 40 and result.stdout == ""


def test_byte_verified_insufficient_report_cannot_promote_admission(tmp_path):
    from fixture_factory import artifact

    from modelvet.application.scan import ScanRequest, ScanService
    from modelvet.reports.audit import verify_report
    from modelvet.reports.json_report import read_report

    source = tmp_path / "serialized-input"
    artifact(source, "serialized")
    result = ScanService().run(ScanRequest(source, tmp_path / "stored", scanner="none"))
    report_path = result.json_path
    original = report_path.read_bytes()
    assert read_report(report_path).decision.state == "INSUFFICIENT"
    verified = verify_report(report_path)
    target = manifest(tmp_path, [report_path])
    batch_result = audit_batch(target, tmp_path)
    assert verified.status == batch_result.status == "VERIFIED"
    assert verified.admission_recomputed is batch_result.admission_recomputed is False
    assert report_path.read_bytes() == original
    assert read_report(report_path).decision.state == "INSUFFICIENT"
