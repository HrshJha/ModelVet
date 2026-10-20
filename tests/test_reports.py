import hashlib
import json
import os
from pathlib import Path

import pytest
from test_policy import evaluate, fixture, policy

from modelvet.core.errors import InvalidInput
from modelvet.coverage.reconciler import CoverageReconciler, expectations_for
from modelvet.evidence.models import EvidenceBundle, MetadataClaim, ToolExecution, ToolInfo
from modelvet.inventory.classify import FileFormat
from modelvet.reports import writer
from modelvet.reports.json_report import (
    Report,
    ReportBuilder,
    RunMetadata,
    parse_report,
    read_report,
    semantic_digest,
    serialize_report,
)
from modelvet.reports.markdown import render_markdown
from modelvet.reports.privacy import redact
from modelvet.reports.writer import ReportWriteError, ReportWriter


@pytest.mark.parametrize(
    "value",
    [
        "Authorization: Bearer TOPSECRET",
        "Authorization: Basic TOPSECRET",
        "https://example.test/?access_token=TOPSECRET&other=ok",
        '{"password": "TOPSECRET with spaces"}',
        '{"password": "TOPSECRET\nwith newline"}',
        "refresh_token=TOPSECRET",
    ],
)
def test_common_credential_patterns_are_fully_redacted(value) -> None:
    assert "TOPSECRET" not in redact(value)


def test_sensitive_detail_keys_are_redacted_without_losing_original_reference() -> None:
    _, _, checks = fixture(FileFormat.SAFETENSORS, FileFormat.JSON)
    checks[-1] = checks[-1].model_copy(
        update={"details": {"password": "TOPSECRET", "access_token": "TOPSECRET"}}
    )
    report = make_report(checks=checks)
    assert "TOPSECRET" not in serialize_report(report).decode()
    assert len([key for key in report.references if key.startswith("check:")]) == len(checks)


@pytest.fixture(autouse=True)
def input_directory(tmp_path):
    (tmp_path / "input").mkdir(exist_ok=True)


def make_report(*, claims=(), raw_payloads=None, executions=(), checks=None):
    manifest, classes, observed = fixture(FileFormat.SAFETENSORS, FileFormat.JSON)
    checks = checks if checks is not None else observed
    selected = policy()
    coverage = CoverageReconciler().reconcile(manifest, expectations_for(manifest, classes), checks)
    decision = evaluate((manifest, classes, checks), claims=claims)
    evidence = EvidenceBundle(
        checks=tuple(checks),
        claims=tuple(claims),
        executions=tuple(executions),
        tools=(
            ToolInfo(tool_id="modelvet", version="0.1.0", source="installed package"),
            *(
                ToolInfo(tool_id=key, version="0.8.8", source="inert test execution")
                for key in sorted({e.tool_id for e in executions})
            ),
        ),
    )
    run = RunMetadata(
        run_id="a" * 32,
        started_at="2026-10-20T00:00:00Z",
        finished_at="2026-10-20T00:00:01Z",
        modelvet_version="0.1.0",
        host_os_family="Darwin",
        result_status="COMPLETE",
    )
    return ReportBuilder().build(
        manifest,
        evidence,
        selected,
        decision,
        run,
        classifications=classes,
        coverage=coverage,
        conflicts=[],
        raw_payloads=raw_payloads,
        private_roots=("/sensitive/root",),
    )


def test_schema_roundtrip_and_reference_index() -> None:
    report = make_report()
    assert parse_report(serialize_report(report)) == report
    assert report.references[report.decision.evidence_refs[0]] == "/artifact"
    assert Report.model_json_schema() == json.loads(
        (Path(__file__).parents[1] / "schemas/report-v1.json").read_text()
    )


def test_redaction_and_escaped_markdown_preserve_identity() -> None:
    manifest, _, _ = fixture(FileFormat.SAFETENSORS, FileFormat.JSON)
    file = manifest.files[1]
    claim = MetadataClaim(
        claim_id="a" * 64,
        kind="LICENSE",
        value=(
            "<script>alert(1)</script> [click](javascript:bad) | "
            "/sensitive/root/file token=TOPSECRET"
        ),
        source_ref="https://name:TOPSECRET@example.test/?token=TOPSECRET",
        source_file_id=file.file_id,
        source_sha256=file.sha256,
    )
    report = make_report(claims=[claim])
    raw = serialize_report(report).decode()
    text = render_markdown(report)
    assert "TOPSECRET" not in raw + text
    assert "/sensitive/root" not in raw + text
    assert "<script>" not in text and "[click](" not in text
    assert "&#60;script&#62;" in text
    assert report.files[1].sha256 == file.sha256


@pytest.mark.parametrize(
    "mutation",
    ["digest", "policy", "unknown", "dangling", "file", "coverage", "duplicate_key", "nan"],
)
def test_invalid_or_tampered_reports_fail(mutation) -> None:
    data = make_report().model_dump(mode="json")
    if mutation == "digest":
        data["semantic_digest"] = "sha256:" + "f" * 64
    elif mutation == "policy":
        data["policy_digest"] = "sha256:" + "f" * 64
    elif mutation == "unknown":
        data["unexpected"] = True
    elif mutation == "dangling":
        data["references"][data["manifest_digest"]] = "/missing/0"
    elif mutation == "file":
        data["files"][0]["size"] += 1
    elif mutation == "coverage":
        data["coverage"] = []
    elif mutation == "nan":
        data["checks"][0]["details"]["number"] = float("nan")
    raw = json.dumps(data).encode()
    if mutation == "duplicate_key":
        raw = raw[:-1] + b',"schema_version":"1.0.0"}'
    with pytest.raises(InvalidInput):
        parse_report(raw)


def test_missing_check_report_is_insufficient_and_cannot_be_promoted() -> None:
    _, _, checks = fixture(FileFormat.SAFETENSORS, FileFormat.JSON)
    report = make_report(checks=checks[:-1])
    assert report.decision.state == "INSUFFICIENT"
    assert any(row.mandatory_unresolved for row in report.coverage)
    data = report.model_dump(mode="json")
    data["decision"]["state"] = "APPROVE"
    data["semantic_digest"] = semantic_digest(data)
    with pytest.raises(InvalidInput):
        parse_report(json.dumps(data).encode())


def test_raw_bytes_have_hash_references_and_missing_or_changed_payload_refused(tmp_path) -> None:
    payload = b"sensitive original scanner stderr"
    digest = hashlib.sha256(payload).hexdigest()
    manifest, _, _ = fixture(FileFormat.SAFETENSORS, FileFormat.JSON)
    execution = ToolExecution(
        execution_id="scan",
        tool_id="modelscan",
        status="FAILED",
        artifact_digest=manifest.manifest_digest,
        stderr_digest=digest,
    )
    with pytest.raises(InvalidInput):
        make_report(executions=[execution])
    report = make_report(executions=[execution], raw_payloads={digest: payload})
    path, _ = ReportWriter().write(
        report, tmp_path / "out", artifact_dir=tmp_path / "input", raw_payloads={digest: payload}
    )
    assert (path.parent / "raw" / (digest + ".bin")).read_bytes() == payload
    assert os.stat(path.parent / "raw" / (digest + ".bin")).st_mode & 0o777 == 0o600
    with pytest.raises(ReportWriteError):
        ReportWriter().write(
            report,
            tmp_path / "other",
            artifact_dir=tmp_path / "input",
            raw_payloads={digest: b"changed"},
        )


def test_private_atomic_nonoverwriting_output(tmp_path) -> None:
    report = make_report()
    path, md = ReportWriter().write(report, tmp_path / "out", artifact_dir=tmp_path / "input")
    assert read_report(path) == report
    assert md is not None and md.exists()
    assert os.stat(path).st_mode & 0o777 == 0o600
    assert os.stat(path.parent).st_mode & 0o777 == 0o700
    before = path.read_bytes()
    with pytest.raises(ReportWriteError):
        ReportWriter().write(report, tmp_path / "out", artifact_dir=tmp_path / "input")
    assert path.read_bytes() == before
    assert not list(path.parent.glob(".*.tmp"))


def test_json_only_and_safe_output_separation(tmp_path) -> None:
    report = make_report()
    with pytest.raises(InvalidInput):
        ReportWriter().write(report, tmp_path / "input/out", artifact_dir=tmp_path / "input")
    with pytest.raises(InvalidInput):
        ReportWriter().write(
            report,
            tmp_path / "snapshot/out",
            artifact_dir=tmp_path / "input",
            snapshot_dir=tmp_path / "snapshot",
        )
    path, md = ReportWriter().write(
        report, tmp_path / "out", artifact_dir=tmp_path / "input", markdown=False
    )
    assert path.exists() and md is None and not path.with_suffix(".md").exists()


def test_output_symlink_and_disk_failure_do_not_publish(tmp_path, monkeypatch) -> None:
    report = make_report()
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    with pytest.raises(InvalidInput):
        ReportWriter().write(report, link / "out", artifact_dir=tmp_path / "input")

    def fail(*args, **kwargs):
        raise OSError("simulated disk full")

    monkeypatch.setattr(writer, "_atomic", fail)
    with pytest.raises(ReportWriteError):
        ReportWriter().write(report, tmp_path / "out", artifact_dir=tmp_path / "input")
    assert not list((tmp_path / "out").rglob("report.json"))


@pytest.mark.parametrize("kind", ["symlink", "fifo", "missing", "directory"])
def test_inspect_reader_rejects_unsafe_files(tmp_path, kind) -> None:
    target = tmp_path / "report.json"
    if kind == "symlink":
        target.symlink_to(tmp_path / "other")
    elif kind == "fifo":
        os.mkfifo(target)
    elif kind == "directory":
        target.mkdir()
    with pytest.raises(InvalidInput):
        read_report(target)
