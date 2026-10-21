"""Cross-interface wiring: real CLI and worker, stored evidence and review workflow."""

import json

import pytest
from fixture_factory import artifact, controlled_policy
from test_cli import invoke
from test_workbench_jobs import wait_job
from workbench_helpers import ui as ui

from modelvet.reports.json_report import parse_report, read_report
from modelvet.reports.markdown import render_markdown


@pytest.mark.parametrize(
    "variant,controls,decision,exit_code",
    [
        ("clean", False, "APPROVE", 0),
        ("clean", True, "CONTROLS", 10),
        ("source", False, "BLOCK", 20),
        ("unknown", False, "INSUFFICIENT", 30),
        ("serialized", False, "INSUFFICIENT", 30),
    ],
)
def test_cli_worker_evidence_export_import_parity(
    ui, tmp_path, variant, controls, decision, exit_code
) -> None:
    client, root, workspace, _ = ui
    source = artifact(root / "candidate", variant)
    body = {"model_path": "candidate", "scanner": "none"}
    arguments = ["scan", str(source), "--out", str(tmp_path / "cli"), "--scanner", "none"]
    if controls:
        selected = controlled_policy(tmp_path / "controls.toml")
        policy = client.post("/api/v1/policies", json={"toml": selected.read_text()})
        assert policy.status_code == 200, policy.text
        body["policy_id"] = policy.json()["id"]
        arguments.extend(["--policy", str(selected)])

    result = invoke(*arguments, "--json-summary")
    assert result.returncode == exit_code, result.stderr
    cli_summary = json.loads(result.stdout)
    assert cli_summary["decision"] == decision
    cli_path = tmp_path / "cli" / cli_summary["report"]
    cli_report = read_report(cli_path)

    response = client.post("/api/v1/scans", json=body)
    assert response.status_code == 202, response.text
    job = wait_job(client, response.json()["id"])
    # Completion is orchestration status; all four admission states are legitimate.
    assert job["status"] == "completed" and job["report_id"] is not None, job
    key = job["report_id"]
    summary = client.get(f"/api/v1/reports/{key}").json()
    assert summary["decision"] == decision
    assert summary["semantic_digest"] == cli_report.semantic_digest

    downloaded = client.get(f"/api/v1/reports/{key}/download")
    assert downloaded.status_code == 200
    report = parse_report(downloaded.content)
    assert report.manifest_digest == cli_report.manifest_digest
    assert report.policy_digest == cli_report.policy_digest
    assert report.decision == cli_report.decision
    assert report.run.run_id != cli_report.run.run_id
    markdown = client.get(f"/api/v1/reports/{key}/download?format=markdown")
    assert markdown.status_code == 200 and markdown.text == render_markdown(report)
    assert cli_path.with_suffix(".md").read_text() == render_markdown(cli_report)

    # Walk the paged review API, rather than assuming summary counts prove coverage.
    for section in ("checks", "coverage", "claims", "conflicts", "references"):
        expected = (
            [{"id": k, "pointer": v} for k, v in sorted(report.references.items())]
            if section == "references"
            else [row.model_dump(mode="json") for row in getattr(report, section)]
        )
        observed = []
        for offset in range(0, max(1, len(expected)), 2):
            page = client.get(
                f"/api/v1/reports/{key}/evidence/{section}",
                params={"offset": offset, "limit": 2},
            )
            assert page.status_code == 200, page.text
            assert page.json()["total"] == len(expected) and not page.json()["truncated"]
            observed.extend(page.json()["items"])
        assert observed == expected
    projection = report.model_dump(mode="json")
    for pointer in report.references.values():
        value = projection
        for part in pointer.lstrip("/").split("/"):
            part = part.replace("~1", "/").replace("~0", "~")
            value = value[int(part)] if isinstance(value, list) else value[part]

    saved = tmp_path / "download.json"
    saved.write_bytes(downloaded.content)
    inspected = invoke("inspect", str(saved), "--format", "json")
    assert inspected.returncode == 0, inspected.stderr
    assert json.loads(inspected.stdout)["semantic_digest"] == report.semantic_digest
    audit = client.post(f"/api/v1/reports/{key}/verify", json={})
    assert audit.status_code == 200 and audit.json()["status"] == "VERIFIED"
    assert audit.json()["admission_recomputed"] is False

    imported = client.post(
        "/api/v1/reports/import",
        content=cli_path.read_bytes(),
        headers={"content-type": "application/json"},
    )
    assert imported.status_code == 201, imported.text
    imported_key = imported.json()["id"]
    comparison = client.post(
        "/api/v1/comparisons", json={"before_id": key, "after_id": imported_key}
    )
    assert comparison.status_code == 200, comparison.text
    assert comparison.json()["same_semantics"] is True
    assert comparison.json()["admission_recomputed"] is False
    imported_audit = client.post(f"/api/v1/reports/{imported_key}/verify", json={}).json()
    assert imported_audit["status"] == ("INCOMPLETE" if report.raw_evidence else "VERIFIED")
    assert client.get(f"/api/v1/reports/{imported_key}").json()["decision"] == decision
    assert client.get("/api/v1/reports").json()["total"] == 2
    assert not list((workspace / "staging").iterdir())
    assert not list((workspace / "tasks").iterdir())


def test_corrected_artifact_rerun_retains_original_gap_and_compares(ui) -> None:
    client, root, _, _ = ui
    source = artifact(root / "candidate", "unknown")

    def run():
        response = client.post("/api/v1/scans", json={"model_path": "candidate", "scanner": "none"})
        assert response.status_code == 202, response.text
        job = wait_job(client, response.json()["id"])
        assert job["status"] == "completed", job
        return job["report_id"]

    before = run()
    assert client.get(f"/api/v1/reports/{before}").json()["decision"] == "INSUFFICIENT"
    unresolved = client.get(f"/api/v1/reports/{before}/evidence/files?status=unresolved").json()
    assert [row["relpath"] for row in unresolved["items"]] == ["opaque.bin"]
    # A legitimate operator correction to this inert fixture, never an automatic repair.
    (source / "opaque.bin").unlink()
    after = run()
    assert client.get(f"/api/v1/reports/{after}").json()["decision"] == "APPROVE"
    assert client.get(f"/api/v1/reports/{before}").json()["decision"] == "INSUFFICIENT"
    comparison = client.post(
        "/api/v1/comparisons",
        json={"before_id": before, "after_id": after, "show_paths": True},
    )
    assert comparison.status_code == 200, comparison.text
    result = comparison.json()
    assert result["same_semantics"] is False and result["changed_file_count"] == 1
    assert result["stored_decision_before"] == "INSUFFICIENT"
    assert result["stored_decision_after"] == "APPROVE"
    assert result["files"][0]["relpath"] == "opaque.bin"
    assert result["admission_recomputed"] is False
