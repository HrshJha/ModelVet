"""Frozen demonstrations are valid synthetic assertions, separate from private history."""

import hashlib
import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from workbench_helpers import ui as ui

from modelvet.reports.json_report import parse_report

DEMO = Path(__file__).parents[1] / "src/modelvet/workbench/demo"


def test_frozen_demo_manifest_matches_reports() -> None:
    manifest = json.loads((DEMO / "manifest.json").read_bytes())
    assert len(manifest["reports"]) == 4
    assert {row["decision"] for row in manifest["reports"]} == {
        "APPROVE",
        "CONTROLS",
        "BLOCK",
        "INSUFFICIENT",
    }
    for row in manifest["reports"]:
        raw = (DEMO / row["file"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row["sha256"]
        report = parse_report(raw)
        assert report.semantic_digest == row["semantic_digest"]
        assert report.decision.state.value == row["decision"]
        assert all(tool.tool_id == "modelvet" for tool in report.tools)
        assert not report.executions  # These examples do not claim scanner validation.
        if row["decision"] == "INSUFFICIENT":
            assert any(item.mandatory_unresolved for item in report.coverage)


def test_demo_api_never_adds_to_history_or_verifies_unsupplied_attachments(ui) -> None:
    client, _, _, _ = ui
    assert client.get("/api/v1/reports").json()["total"] == 0
    demos = client.get("/api/v1/demos").json()
    assert len(demos) == 4 and all(row["demo"] for row in demos)
    for row in demos:
        key = row["id"]
        assert "Demonstration" in row["label"]
        assert client.get(f"/api/v1/reports/{key}").json()["demo"]
        raw = client.get(f"/api/v1/reports/{key}/download").content
        assert parse_report(raw).semantic_digest == row["semantic_digest"]
        assert client.get(f"/api/v1/reports/{key}/evidence/files").status_code == 200
        assert client.post(f"/api/v1/reports/{key}/verify", json={}).status_code == 400
    assert client.get("/api/v1/reports").json()["total"] == 0
