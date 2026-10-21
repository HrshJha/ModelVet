"""T-HF-COV-01: same engine/decisions, every omitted path retains required gaps."""

import pytest
from fixture_factory import artifact, controlled_policy
from hub_fixtures import URL, FakeHTTPS

from modelvet.application.scan import ScanRequest, ScanService
from modelvet.core.limits import ScanLimits
from modelvet.hub import assessment
from modelvet.hub.assessment import scan_hub
from modelvet.reports.json_report import parse_report, serialize_report


@pytest.mark.parametrize(
    "variant,expected",
    [
        ("clean", "APPROVE"),
        ("source", "BLOCK"),
        ("malformed", "INSUFFICIENT"),
        ("unknown", "INSUFFICIENT"),
        ("serialized", "INSUFFICIENT"),
        ("controls", "CONTROLS"),
    ],
)
def test_same_static_engine_and_decisions(tmp_path, monkeypatch, variant, expected):
    root = artifact(tmp_path / "input", "clean" if variant == "controls" else variant)
    policy = controlled_policy(tmp_path / "controls.toml") if variant == "controls" else None
    files = {p.name: p.read_bytes() for p in root.iterdir()}
    monkeypatch.setattr(assessment, "HTTPS", lambda **kwargs: FakeHTTPS(files))
    local = ScanService().run(ScanRequest(root, tmp_path / "local", policy, "none"))
    stages = []
    remote = scan_hub(
        URL,
        output_dir=tmp_path / "remote",
        policy_path=policy,
        scanner="none",
        on_progress=stages.append,
    )
    assert local.report.decision.state == remote.report.decision.state == expected
    assert local.report.checks == remote.report.checks
    assert local.report.coverage == remote.report.coverage
    assert local.report.manifest_digest == remote.report.manifest_digest
    assert local.report.schema_version == "1.0.0" and "source" not in local.report.model_dump()
    assert remote.report.schema_version == "2.0.0" and remote.report.source.complete
    assert parse_report(serialize_report(remote.report)) == remote.report
    assert stages[:2] == ["hub_inventory", "hub_retrieval"]


def test_unfetched_file_cannot_approve_or_disappear(tmp_path, monkeypatch):
    root = artifact(tmp_path / "input")
    files = {p.name: p.read_bytes() for p in root.iterdir()}
    files["large.safetensors"] = b"x" * 1000
    monkeypatch.setattr(assessment, "HTTPS", lambda **kwargs: FakeHTTPS(files))
    outcome = scan_hub(URL, output_dir=tmp_path / "out", limits=ScanLimits(max_file_bytes=500))
    assert outcome.report.decision.state == "INSUFFICIENT"
    missing = next(f for f in outcome.report.source.files if f.path == "large.safetensors")
    assert missing.status == "OVERSIZED"
    assert "structural:safetensors" in missing.required_checks
    assert "large.safetensors" not in {f.relpath for f in outcome.report.files}
    assert "hub:source" in outcome.report.decision.evidence_refs
    assert outcome.report.source.files[-1].path == "weights.safetensors"


def test_repeated_remote_evidence_is_semantically_stable(tmp_path, monkeypatch):
    root = artifact(tmp_path / "input")
    files = {p.name: p.read_bytes() for p in root.iterdir()}
    monkeypatch.setattr(assessment, "HTTPS", lambda **kwargs: FakeHTTPS(files))
    first = scan_hub(URL, output_dir=tmp_path / "one")
    second = scan_hub(URL, output_dir=tmp_path / "two")
    assert first.report.semantic_digest == second.report.semantic_digest


def test_independent_source_ban_survives_unrelated_retrieval_gap(tmp_path, monkeypatch):
    root = artifact(tmp_path / "input", "source")
    files = {p.name: p.read_bytes() for p in root.iterdir()}
    files["z.bin"] = b"x" * 1000
    monkeypatch.setattr(assessment, "HTTPS", lambda **kwargs: FakeHTTPS(files))
    report = scan_hub(
        URL, output_dir=tmp_path / "out", limits=ScanLimits(max_file_bytes=500)
    ).report
    assert report.decision.state == "BLOCK"
    assert any(f.status == "OVERSIZED" for f in report.source.files)


@pytest.mark.parametrize("enabled", [False, True])
def test_only_selected_token_reaches_transport_never_report(tmp_path, monkeypatch, enabled):
    root = artifact(tmp_path / "input")
    files = {p.name: p.read_bytes() for p in root.iterdir()}
    secret = "hf_PRIVATETOKEN1234"
    monkeypatch.setenv("HF_TOKEN", secret)

    def transport(**kwargs):
        assert kwargs["token"] == (secret if enabled else None)
        return FakeHTTPS(files)

    monkeypatch.setattr(assessment, "HTTPS", transport)
    report = scan_hub(URL, use_hf_token=enabled, output_dir=tmp_path / "out").report
    assert secret not in serialize_report(report).decode()
