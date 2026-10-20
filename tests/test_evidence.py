import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from pydantic import ValidationError

from modelvet.evidence.models import (
    CheckRecord,
    CheckResult,
    CheckStatus,
    EvidenceBundle,
    ToolExecution,
)
from modelvet.evidence.normalize import EvidenceNormalizer
from modelvet.inventory.classify import FileClassification, FileFormat, applicable_checks
from modelvet.inventory.discover import FileObservation
from modelvet.inventory.identity import manifest_from_entries
from modelvet.scanners.base import RawScannerExecution, ToolInfo


def fixture(
    scanned: list[str] | None = None,
    skipped: list[str] | None = None,
    issues: list[dict[str, str]] | None = None,
    kind: FileFormat = FileFormat.PICKLE_LIKE,
):
    manifest = manifest_from_entries(
        (FileObservation("weights.pkl", 4, hashlib.sha256(b"data").hexdigest()),)
    )
    (file,) = manifest.files
    issue_list = issues or []
    payload = {
        "summary": {
            "total_issues_by_severity": {
                severity: sum(issue["severity"] == severity for issue in issue_list)
                for severity in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
            },
            "total_issues": len(issue_list),
            "input_path": "/frozen-snapshot",
            "absolute_path": "/frozen-snapshot",
            "modelscan_version": "0.8.8",
            "timestamp": "vendor-observation",
            "scanned": {"total_scanned": len(scanned or []), "scanned_files": scanned or []},
            "skipped": {
                "total_skipped": len(skipped or []),
                "skipped_files": [
                    {"category": "SCAN_NOT_SUPPORTED", "description": "not inspected", "source": p}
                    for p in skipped or []
                ],
            },
        },
        "issues": issue_list,
        "errors": [],
    }
    raw = RawScannerExecution(
        manifest.manifest_digest,
        ToolInfo("modelscan", "0.8.8", "fixture", "0" * 64),
        "COMPLETE",
        ("/trusted-scanner", "-p", "/frozen-snapshot"),
        1 if issues else 0,
        report=json.dumps(payload).encode(),
        environment_digest="0" * 64,
        limitations=(),
    )
    classes = {file.file_id: FileClassification(kind, applicable_checks(kind))}
    return manifest, raw, classes


def modelscan_check(checks: list[CheckRecord]) -> CheckRecord:
    return next(check for check in checks if check.check_id == "modelscan")


def test_complete_proof_binds_hash_and_no_findings() -> None:
    manifest, raw, classes = fixture(["weights.pkl"])
    executions, checks, findings = EvidenceNormalizer().normalize(manifest, raw, classes)
    check = modelscan_check(checks)
    assert check.status == CheckStatus.COMPLETE and check.result == CheckResult.NO_FINDINGS
    assert (
        check.file_id == manifest.files[0].file_id
        and check.artifact_digest == manifest.manifest_digest
    )
    assert check.raw_ref == "sha256:" + hashlib.sha256(raw.report).hexdigest()
    assert executions[0].status == "COMPLETE" and findings == []


@pytest.mark.parametrize(
    "variant,expected",
    [
        ("missing", CheckStatus.INCONCLUSIVE),
        ("skipped", CheckStatus.SKIPPED),
        ("contradiction", CheckStatus.INCONCLUSIVE),
        ("archive", CheckStatus.INCONCLUSIVE),
        ("no-context", CheckStatus.INCONCLUSIVE),
        ("failed", CheckStatus.FAILED),
        ("unsupported", CheckStatus.UNSUPPORTED),
    ],
)
def test_coverage_states_cannot_become_clean(variant: str, expected: CheckStatus) -> None:
    manifest, raw, classes = fixture(
        ["weights.pkl"] if variant != "missing" else [],
        ["weights.pkl"] if variant in {"skipped", "contradiction"} else [],
    )
    if variant == "skipped":
        manifest, raw, classes = fixture([], ["weights.pkl"])
    if variant == "archive":
        manifest, raw, classes = fixture(["weights.pkl"], kind=FileFormat.PYTORCH_ZIP)
    if variant == "no-context":
        classes = {}
    if variant in {"failed", "unsupported"}:
        raw = replace(
            raw,
            status="FAILED" if variant == "failed" else "UNSUPPORTED",
            exit_code=2 if variant == "failed" else 3,
        )
    _, checks, _ = EvidenceNormalizer().normalize(manifest, raw, classes)
    check = modelscan_check(checks)
    assert check.status == expected and check.result == CheckResult.UNKNOWN


@pytest.mark.parametrize("variant", ["schema", "version", "file-id", "path", "digest", "counts"])
def test_invalid_scanner_payload_fails_closed(variant: str) -> None:
    manifest, raw, classes = fixture(["weights.pkl"])
    data = json.loads(raw.report)
    if variant == "schema":
        data = {}
    if variant == "version":
        data["summary"]["modelscan_version"] = "9.0"
    if variant == "file-id":
        data["summary"]["scanned"]["scanned_files"] = ["missing.pkl"]
    if variant == "path":
        data["summary"]["scanned"]["scanned_files"] = ["../escape"]
    if variant == "counts":
        data["summary"]["scanned"]["total_scanned"] = 100
    raw = replace(raw, report=json.dumps(data).encode())
    if variant == "digest":
        raw = replace(raw, artifact_digest="sha256:" + "f" * 64)
    executions, checks, _ = EvidenceNormalizer().normalize(manifest, raw, classes)
    assert executions[0].status == "FAILED"
    assert modelscan_check(checks).status == CheckStatus.FAILED


def test_scanner_findings_are_only_reported() -> None:
    issue = {
        "description": "reported operator",
        "module": "os",
        "operator": "system",
        "source": "weights.pkl",
        "scanner": "fixture-engine",
        "severity": "HIGH",
    }
    manifest, raw, classes = fixture(["weights.pkl"], issues=[issue])
    _, checks, findings = EvidenceNormalizer().normalize(manifest, raw, classes)
    assert modelscan_check(checks).result == CheckResult.FINDINGS
    assert findings[0].verification_state.value == "REPORTED"


def test_missing_scanner_and_unenforced_resources() -> None:
    manifest, raw, classes = fixture(["weights.pkl"])
    missing = replace(raw, tool=None, status="NOT_RUN", report=b"", argv=(), reason="unavailable")
    _, checks, _ = EvidenceNormalizer().normalize(manifest, missing, classes)
    assert all(check.status == CheckStatus.NOT_RUN for check in checks)
    limited = replace(raw, limitations=("macOS scanner memory is not OS-bounded.",))
    _, checks, _ = EvidenceNormalizer().normalize(manifest, limited, classes)
    assert (
        next(check for check in checks if check.check_id == "scanner:resources").status
        == CheckStatus.UNSUPPORTED
    )


def test_wire_unknown_status_extra_fields_and_failed_clean_rejected() -> None:
    manifest, raw, classes = fixture(["weights.pkl"])
    _, checks, _ = EvidenceNormalizer().normalize(manifest, raw, classes)
    data = checks[0].model_dump(mode="json")
    for changes in ({"status": "NEW_UNKNOWN"}, {"unexpected": 1}, {"status": "FAILED"}):
        with pytest.raises(ValidationError):
            CheckRecord.model_validate_json(json.dumps({**data, **changes}))


def test_schema_snapshot() -> None:
    expected = json.loads((Path(__file__).parents[1] / "schemas/evidence-v1.json").read_text())
    assert EvidenceBundle.model_json_schema() == expected


@pytest.mark.parametrize("timestamp", ["2026-10-20T01:00:00", "2026-10-20T01:00:00+05:30", "bad"])
def test_normalized_timestamps_must_be_utc(timestamp: str) -> None:
    manifest, raw, classes = fixture(["weights.pkl"])
    executions, _, _ = EvidenceNormalizer().normalize(manifest, raw, classes)
    data = executions[0].model_dump(mode="json")
    with pytest.raises(ValidationError):
        ToolExecution.model_validate_json(json.dumps({**data, "started_at": timestamp}))
    valid = ToolExecution.model_validate_json(
        json.dumps({**data, "started_at": "2026-10-20T00:00:00Z"})
    )
    assert valid.started_at == "2026-10-20T00:00:00Z"


def test_nonfinite_normalized_details_rejected() -> None:
    manifest, raw, classes = fixture(["weights.pkl"])
    _, checks, _ = EvidenceNormalizer().normalize(manifest, raw, classes)
    data = checks[0].model_dump(mode="json")
    with pytest.raises(ValidationError):
        CheckRecord.model_validate_json(json.dumps({**data, "details": {"value": float("nan")}}))
