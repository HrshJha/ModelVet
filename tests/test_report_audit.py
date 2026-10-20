import hashlib
import json
import os
from pathlib import Path

import pytest
from pydantic import ValidationError
from test_cli import invoke
from test_reports import make_report

from modelvet.core.errors import InvalidInput
from modelvet.reports import audit
from modelvet.reports.audit import ReportAudit, verify_report
from modelvet.reports.writer import ReportWriter


def saved(tmp_path, payloads=(b"original private evidence",)):
    source = tmp_path / "input"
    source.mkdir(exist_ok=True)
    raw = {hashlib.sha256(value).hexdigest(): value for value in payloads}
    report = make_report(raw_payloads=raw)
    path, _ = ReportWriter().write(
        report, tmp_path / "reports", artifact_dir=source, raw_payloads=raw
    )
    return path, report


def test_declared_raw_evidence_verified_without_reading_models(tmp_path):
    path, report = saved(tmp_path)
    result = verify_report(path)
    assert result.status == "VERIFIED" and result.verified_attachments == 1
    assert result.raw_bytes_read == report.raw_evidence[0].size
    assert result.admission_recomputed is False
    assert "not a signature" in result.notice
    assert ReportAudit.model_validate_json(result.model_dump_json()) == result
    assert str(tmp_path) not in result.model_dump_json()


@pytest.mark.parametrize("payloads", [(), (b"",)])
def test_no_raw_or_zero_length_bytes(tmp_path, payloads):
    path, _ = saved(tmp_path, payloads)
    result = verify_report(path, max_raw_bytes=0)
    assert result.status == "VERIFIED" and result.raw_bytes_read == 0


@pytest.mark.parametrize(
    "variant,status",
    [
        ("missing", "MISSING"),
        ("hash", "HASH_MISMATCH"),
        ("size", "SIZE_MISMATCH"),
        ("symlink", "UNSAFE"),
        ("hardlink", "UNSAFE"),
        ("fifo", "UNSAFE"),
        ("raw-link", "UNSAFE"),
        ("raw-missing", "MISSING"),
    ],
)
def test_untrusted_raw_files_never_verify(tmp_path, variant, status):
    path, report = saved(tmp_path)
    target = path.parent / report.raw_evidence[0].filename
    original = target.read_bytes()
    if variant == "missing":
        target.unlink()
    elif variant == "hash":
        target.write_bytes(b"X" * len(original))
    elif variant == "size":
        target.write_bytes(b"X")
    elif variant == "symlink":
        outside = tmp_path / "outside"
        outside.write_bytes(original)
        target.unlink()
        target.symlink_to(outside)
    elif variant == "hardlink":
        os.link(target, tmp_path / "other-link")
    elif variant == "fifo":
        target.unlink()
        os.mkfifo(target)
    else:
        directory = path.parent / "raw"
        directory.rename(path.parent / "moved")
        if variant == "raw-link":
            directory.symlink_to(path.parent / "moved", target_is_directory=True)
    result = verify_report(path)
    assert result.status == "INCOMPLETE" and result.unresolved_attachments == 1
    assert result.attachments[0].status == status


def test_external_report_pin_and_no_writes(tmp_path):
    path, _ = saved(tmp_path)
    original = path.read_bytes()
    pin = hashlib.sha256(original).hexdigest()
    assert verify_report(path, expected_report_sha256=pin).status == "VERIFIED"
    assert verify_report(path, expected_report_sha256="f" * 64).status == "INCOMPLETE"
    assert path.read_bytes() == original
    with pytest.raises(InvalidInput):
        verify_report(path, expected_report_sha256="not-a-sha")


def test_count_and_aggregate_byte_budgets(tmp_path):
    path, _ = saved(tmp_path, tuple(str(i).encode() for i in range(65)))
    result = verify_report(path)
    assert result.status == "INCOMPLETE" and result.omitted_attachments == 1
    assert len(result.attachments) == 64
    result = verify_report(path, max_raw_bytes=0)
    assert result.raw_bytes_read == 0 and result.status == "INCOMPLETE"
    assert all(row.status == "BUDGET_EXCEEDED" for row in result.attachments)


@pytest.mark.parametrize(
    "options",
    [
        {"max_raw_bytes": -1},
        {"max_raw_bytes": True},
        {"max_raw_bytes": 33 * 1024 * 1024},
        {"max_attachments": 65},
    ],
)
def test_invalid_budgets(tmp_path, options):
    path, _ = saved(tmp_path)
    with pytest.raises(InvalidInput):
        verify_report(path, **options)


def test_raw_identity_drift(tmp_path, monkeypatch):
    path, _ = saved(tmp_path)
    original = audit.stat_identity
    count = 0

    def different(value):
        nonlocal count
        count += 1
        return (*original(value), count)

    monkeypatch.setattr(audit, "stat_identity", different)
    result = verify_report(path)
    assert result.status == "INCOMPLETE" and result.attachments[0].status == "CHANGED"


@pytest.mark.parametrize("second_failure", [False, True])
def test_report_recheck_drift_or_missing(tmp_path, monkeypatch, second_failure):
    path, _ = saved(tmp_path)
    original = audit.read_report_bytes
    count = 0

    def changed(selected, **kwargs):
        nonlocal count
        count += 1
        if count > 1 and second_failure:
            raise InvalidInput("Injected disappearance")
        return original(selected, **kwargs) + (b" " if count > 1 else b"")

    monkeypatch.setattr(audit, "read_report_bytes", changed)
    assert verify_report(path).status == "INCOMPLETE"


def test_audit_schema_and_forged_counts(tmp_path):
    root = Path(__file__).parents[1]
    assert ReportAudit.model_json_schema() == json.loads(
        (root / "schemas/report-audit-v1.json").read_text()
    )
    path, _ = saved(tmp_path)
    data = verify_report(path).model_dump(mode="json")
    data["verified_attachments"] = 0
    with pytest.raises(ValidationError):
        ReportAudit.model_validate_json(json.dumps(data))


def test_verify_cli_exit_classes(tmp_path):
    path, report = saved(tmp_path)
    result = invoke("verify", str(path))
    assert result.returncode == 0 and json.loads(result.stdout)["status"] == "VERIFIED"
    assert str(tmp_path) not in result.stdout + result.stderr
    (path.parent / report.raw_evidence[0].filename).unlink()
    result = invoke("verify", str(path))
    assert result.returncode == 30 and json.loads(result.stdout)["status"] == "INCOMPLETE"
    path.write_text("invalid report")
    result = invoke("verify", str(path))
    assert result.returncode == 40 and result.stdout == ""
