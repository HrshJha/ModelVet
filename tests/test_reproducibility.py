import hashlib
import json

import pytest
from test_policy import evaluate
from test_reports import make_report

from modelvet.core.limits import ScanLimits
from modelvet.core.snapshot import Snapshotter
from modelvet.evidence.models import CheckRecord, CheckResult, CheckStatus, ToolExecution
from modelvet.inventory.classify import Classifier
from modelvet.inventory.gate import InputGate
from modelvet.inventory.identity import InventoryService, final_identity_checks
from modelvet.reports.json_report import parse_report, semantic_digest


def test_run_timestamps_ids_and_raw_observations_do_not_change_semantics() -> None:
    first = make_report().model_dump(mode="json")
    second = json.loads(json.dumps(first))
    second["run"]["run_id"] = "b" * 32
    second["run"]["started_at"] = "2026-10-21T00:00:00Z"
    second["run"]["finished_at"] = "2026-10-21T00:01:00Z"
    assert semantic_digest(first) == semantic_digest(second)
    second["semantic_digest"] = semantic_digest(second)
    assert parse_report(json.dumps(second).encode()).semantic_digest == first["semantic_digest"]


def test_raw_vendor_timestamp_and_environment_hash_do_not_change_semantics() -> None:
    reports = []
    for stamp in ("first", "second"):
        payload = json.dumps({"timestamp": stamp}).encode()
        digest = hashlib.sha256(payload).hexdigest()
        base = make_report()
        execution = ToolExecution(
            execution_id="scan",
            tool_id="modelscan",
            status="FAILED",
            artifact_digest=base.manifest_digest,
            raw_report_digest=digest,
            environment_digest=hashlib.sha256(stamp.encode()).hexdigest(),
        )
        reports.append(make_report(executions=[execution], raw_payloads={digest: payload}))
    assert reports[0].semantic_digest == reports[1].semantic_digest
    assert reports[0].raw_evidence != reports[1].raw_evidence


def test_semantic_change_changes_digest() -> None:
    first = make_report().model_dump(mode="json")
    second = json.loads(json.dumps(first))
    second["limitations"].append("New bounded check limitation.")
    assert semantic_digest(first) != semantic_digest(second)
    second = json.loads(json.dumps(first))
    second["tools"][0]["version"] = "0.1.1"
    assert semantic_digest(first) != semantic_digest(second)


@pytest.mark.parametrize("mutation", ["none", "source", "snapshot", "added_file", "deleted_file"])
def test_final_identity_recheck_prevents_stale_admission(tmp_path, mutation) -> None:
    root = tmp_path / "input"
    root.mkdir()
    header = b'{"x":{"dtype":"F32","shape":[1],"data_offsets":[0,4]}}'
    (root / "weights.safetensors").write_bytes(
        len(header).to_bytes(8, "little") + header + b"\0" * 4
    )
    source = InputGate().validate(root, tmp_path / "out", ScanLimits())
    with Snapshotter().create(source) as snapshot:
        manifest = InventoryService().collect(snapshot)
        classes = {file.file_id: Classifier().classify(file, snapshot) for file in manifest.files}
        file = manifest.files[0]
        checks = [
            CheckRecord(
                file_id=file.file_id,
                check_id=key,
                executor_id="modelvet",
                status=CheckStatus.COMPLETE,
                result=CheckResult.NO_FINDINGS,
                artifact_digest=manifest.manifest_digest,
                details=details,
            )
            for key, details in (
                ("identity", {"sha256": file.sha256}),
                ("classification", {"format_class": "SAFETENSORS", "mismatch": False}),
                ("structural:safetensors", {}),
            )
        ]
        assert evaluate((manifest, classes, checks)).state == "APPROVE"
        if mutation == "source":
            (root / "weights.safetensors").write_bytes(b"changed")
        elif mutation == "snapshot":
            path = snapshot.root / "weights.safetensors"
            path.chmod(0o600)
            path.write_bytes(b"changed")
        elif mutation == "added_file":
            (root / "new").write_text("added")
        elif mutation == "deleted_file":
            (root / "weights.safetensors").unlink()
        updated = final_identity_checks(snapshot, manifest, checks)
        assert evaluate((manifest, classes, updated)).state == (
            "APPROVE" if mutation == "none" else "INSUFFICIENT"
        )
        assert checks[0].status == CheckStatus.COMPLETE
