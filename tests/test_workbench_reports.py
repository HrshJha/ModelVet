"""FR-026 pinned report presentation/import/comparison acceptance."""

import hashlib
import json

import pytest
from fixture_factory import artifact

pytest.importorskip("fastapi")
from workbench_helpers import ui as ui

from modelvet.application.scan import ScanRequest, ScanService
from modelvet.reports.json_report import semantic_digest


def saved(ui, variant="clean"):
    _, root, workspace, app = ui
    name = f"artifact-{len(list(root.iterdir()))}"
    source = artifact(root / name, variant)
    outcome = ScanService().run(ScanRequest(source, workspace / "reports" / name, scanner="none"))
    summary = app.state.store.add_report(outcome.json_path, name, model_path=name)
    return summary.id, outcome


def test_evidence_pages_search_and_coverage(ui) -> None:
    client, _, _, _ = ui
    key, outcome = saved(ui, "unknown")
    response = client.get(f"/api/v1/reports/{key}/evidence/files", params={"limit": 1})
    assert response.status_code == 200
    page = response.json()
    assert page["total"] == len(outcome.report.files) and len(page["items"]) == 1
    assert "coverage" in page["items"][0]
    unresolved = client.get(f"/api/v1/reports/{key}/evidence/files?status=unresolved").json()
    assert any(row["relpath"] == "opaque.bin" for row in unresolved["items"])
    matched = client.get(f"/api/v1/reports/{key}/evidence/files?q=weights").json()
    assert len(matched["items"]) == 1
    file_id = matched["items"][0]["file_id"]
    checks = client.get(
        f"/api/v1/reports/{key}/evidence/checks", params={"file_id": file_id}
    ).json()
    assert checks["items"] and all(row["file_id"] == file_id for row in checks["items"])
    assert client.get(f"/api/v1/reports/{key}/evidence/files?file_id=../escape").status_code == 400


def test_import_download_preserves_exact_original_bytes(ui) -> None:
    client, _, _, _ = ui
    _, outcome = saved(ui)
    original = b"\n" + outcome.json_path.read_bytes() + b"\n"
    response = client.post(
        "/api/v1/reports/import", content=original, headers={"content-type": "application/json"}
    )
    assert response.status_code == 201, response.text
    key = response.json()["id"]
    downloaded = client.get(f"/api/v1/reports/{key}/download")
    assert downloaded.content == original
    assert (
        downloaded.headers["content-disposition"] == f'attachment; filename="modelvet-{key}.json"'
    )
    assert client.get(f"/api/v1/reports/{key}/download?format=markdown").status_code == 200
    assert client.get("/api/v1/reports").json()["total"] == 2


def test_malformed_and_tampered_reports_do_not_open(ui) -> None:
    client, _, _, app = ui
    assert client.post("/api/v1/reports/import", json={}).status_code == 400
    key, outcome = saved(ui)
    assert client.get(f"/api/v1/reports/{key}").status_code == 200
    original = outcome.json_path.read_bytes()
    outcome.json_path.write_bytes(original + b"\n")
    for suffix in ("", "/download", "/evidence/files"):
        assert client.get(f"/api/v1/reports/{key}{suffix}").status_code == 400
    assert client.post(f"/api/v1/reports/{key}/verify", json={}).status_code == 400
    assert app.state.store.query("SELECT COUNT(*) FROM reports")[0][0] == 1
    assert client.get("/api/v1/reports").status_code == 400


def test_verify_and_compare_do_not_promote_admission(ui) -> None:
    client, _, _, _ = ui
    old, _ = saved(ui, "clean")
    new, _ = saved(ui, "unknown")
    audit = client.post(f"/api/v1/reports/{new}/verify", json={}).json()
    assert audit["status"] == "VERIFIED" and audit["admission_recomputed"] is False
    assert client.get(f"/api/v1/reports/{new}").json()["decision"] == "INSUFFICIENT"
    comparison = client.post("/api/v1/comparisons", json={"before_id": old, "after_id": new}).json()
    assert comparison["same_semantics"] is False and comparison["changed_file_count"] == 1
    assert comparison["stored_decision_before"] == "APPROVE"
    assert comparison["stored_decision_after"] == "INSUFFICIENT"
    assert all(row["relpath"] is None for row in comparison["files"])
    assert comparison["admission_recomputed"] is False
    named = client.post(
        "/api/v1/comparisons", json={"before_id": old, "after_id": new, "show_paths": True}
    ).json()
    assert named["files"][0]["relpath"] == "opaque.bin"


def test_imported_missing_raw_attachments_remain_incomplete(ui) -> None:
    client, _, _, _ = ui
    _, outcome = saved(ui)
    data = outcome.report.model_dump(mode="json")
    raw = b"inert absent attachment"
    digest = hashlib.sha256(raw).hexdigest()
    data["raw_evidence"] = [{"digest": digest, "size": len(raw), "filename": f"raw/{digest}.bin"}]
    data["references"]["raw:" + digest] = "/raw_evidence/0"
    data["semantic_digest"] = semantic_digest(data)
    response = client.post(
        "/api/v1/reports/import",
        content=json.dumps(data),
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 201, response.text
    audit = client.post(f"/api/v1/reports/{response.json()['id']}/verify", json={}).json()
    assert audit["status"] == "INCOMPLETE" and audit["verified_attachments"] == 0


def test_index_summary_cannot_promote_a_report(ui) -> None:
    client, _, _, app = ui
    key, _ = saved(ui, "unknown")
    cached = json.loads(
        app.state.store.query("SELECT summary FROM reports WHERE id = ?", (key,))[0][0]
    )
    cached["decision"] = "APPROVE"
    cached["required_complete"] = cached["required_total"]
    app.state.store.query("UPDATE reports SET summary = ? WHERE id = ?", (json.dumps(cached), key))
    assert client.get(f"/api/v1/reports/{key}").json()["decision"] == "INSUFFICIENT"
    assert client.get("/api/v1/reports").json()["items"][0]["decision"] == "INSUFFICIENT"
