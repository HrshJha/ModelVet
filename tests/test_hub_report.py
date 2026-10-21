"""T-HF-REPORT-01: source identity, legacy reads, comparisons and incomplete-proof guard."""

import json

import pytest
from fixture_factory import artifact
from hub_fixtures import URL, FakeHTTPS

from modelvet.application.scan import ScanRequest, ScanService
from modelvet.core.errors import InvalidInput
from modelvet.hub import assessment
from modelvet.hub.assessment import scan_hub
from modelvet.reports.compare import compare_reports
from modelvet.reports.json_report import parse_report, semantic_digest
from modelvet.reports.markdown import render_markdown


def make_remote(tmp_path, monkeypatch):
    root = artifact(tmp_path / "input")
    monkeypatch.setattr(
        assessment,
        "HTTPS",
        lambda **kwargs: FakeHTTPS({p.name: p.read_bytes() for p in root.iterdir()}),
    )
    return root, scan_hub(URL, output_dir=tmp_path / "out")


def test_v1_v2_comparison_both_directions_and_private_markdown(tmp_path, monkeypatch):
    root, remote = make_remote(tmp_path, monkeypatch)
    local = ScanService().run(ScanRequest(root, tmp_path / "local"))
    for left, right in [(local, remote), (remote, local)]:
        comparison = compare_reports(left.json_path, right.json_path)
        assert comparison.same_artifact and not comparison.same_semantics
        assert "source" in comparison.changed_sections
    md = render_markdown(remote.report)
    assert "Hugging Face source" in md and remote.report.source.resolved_commit in md
    assert str(tmp_path) not in md


@pytest.mark.parametrize("change", ["hash", "missing", "v1", "duplicate"])
def test_invalid_source_binding_is_rejected(tmp_path, monkeypatch, change):
    _, remote = make_remote(tmp_path, monkeypatch)
    data = remote.report.model_dump(mode="json")
    if change == "hash":
        data["source"]["files"][0]["sha256"] = "0" * 64
    elif change == "missing":
        data["source"]["files"].pop()
    elif change == "v1":
        data["schema_version"] = "1.0.0"
    else:
        data["source"]["files"].append(data["source"]["files"][0])
    data["semantic_digest"] = semantic_digest(data)
    with pytest.raises(InvalidInput):
        parse_report(json.dumps(data).encode())


def test_inventory_omission_cannot_forge_approve(tmp_path, monkeypatch):
    _, remote = make_remote(tmp_path, monkeypatch)
    data = remote.report.model_dump(mode="json")
    extra = dict(data["source"]["files"][-1])
    extra.update(path="z.bin", sha256=None, status="OVERSIZED")
    data["source"]["files"].append(extra)
    data["semantic_digest"] = semantic_digest(data)
    with pytest.raises(InvalidInput):
        parse_report(json.dumps(data).encode())


def test_observation_metadata_digest_does_not_change_semantics(tmp_path, monkeypatch):
    _, remote = make_remote(tmp_path, monkeypatch)
    data = remote.report.model_dump(mode="json")
    data["source"]["metadata_digest"] = "0" * 64
    assert semantic_digest(data) == remote.report.semantic_digest
    assert parse_report(json.dumps(data).encode()).source.metadata_digest == "0" * 64


def test_remote_pair_applicability_cannot_be_rewritten(tmp_path, monkeypatch):
    _, remote = make_remote(tmp_path, monkeypatch)
    data = remote.report.model_dump(mode="json")
    row = next(f for f in data["source"]["files"] if f["path"] == "weights.safetensors")
    row["required_checks"] = ["identity", "classification"]
    data["semantic_digest"] = semantic_digest(data)
    with pytest.raises(InvalidInput):
        parse_report(json.dumps(data).encode())
