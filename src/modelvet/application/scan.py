"""Local static assessment from private input snapshot to completed report."""

import hashlib
import platform
import tempfile
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from modelvet import __version__
from modelvet.core.config import load_policy
from modelvet.core.limits import ScanLimits
from modelvet.core.snapshot import Snapshotter
from modelvet.coverage.conflicts import ConflictDetector
from modelvet.coverage.reconciler import CoverageReconciler, expectations_for
from modelvet.dependencies.manifest import DependencyReader
from modelvet.evidence.models import (
    CheckRecord,
    CheckResult,
    CheckStatus,
    ConflictRecord,
    CoverageRecord,
    DependencyRecord,
    EvidenceBundle,
    Finding,
    MetadataClaim,
    ToolExecution,
    ToolInfo,
)
from modelvet.evidence.normalize import EvidenceNormalizer, normalize_inspection
from modelvet.inventory.classify import Classifier, FileFormat, applicable_checks
from modelvet.inventory.gate import InputGate
from modelvet.inventory.identity import InventoryService, final_identity_checks
from modelvet.metadata.claims import MetadataReader
from modelvet.policies.evaluator import AdmissionEvaluator
from modelvet.policies.models import AdmissionDecision
from modelvet.reports.json_report import Report, ReportBuilder, RunMetadata
from modelvet.reports.writer import ReportWriter
from modelvet.scanners.base import RawScannerExecution
from modelvet.scanners.modelscan import ModelScanAdapter
from modelvet.structural.safetensors import SafetensorsInspector
from modelvet.structural.zip_index import ZipIndexInspector


@dataclass(frozen=True)
class ScanRequest:
    artifact_dir: Path
    output_dir: Path | None = None
    policy_path: Path | None = None
    scanner: Literal["auto", "modelscan", "none"] = "auto"
    limits: ScanLimits = ScanLimits()
    markdown: bool = True


@dataclass(frozen=True)
class ScanOutcome:
    report: Report
    json_path: Path
    markdown_path: Path | None
    output_root: Path


class ScanService:
    def run(self, request: ScanRequest) -> ScanOutcome:
        started = datetime.now(UTC).isoformat()
        policy = load_policy(request.policy_path)
        source = InputGate().validate(request.artifact_dir, request.output_dir, request.limits)
        payloads: dict[str, bytes] = {}
        with Snapshotter().create(source) as snapshot:
            manifest = InventoryService().collect(snapshot)
            classes = {
                file.file_id: Classifier().classify(file, snapshot) for file in manifest.files
            }
            checks: list[CheckRecord] = []
            tools = [ToolInfo(tool_id="modelvet", version=__version__, source="installed package")]
            for file in manifest.files:
                kind = classes[file.file_id]
                status = (
                    CheckStatus.UNSUPPORTED
                    if kind.mismatch
                    or kind.format_class in {FileFormat.UNKNOWN, FileFormat.BINARY_UNKNOWN}
                    else CheckStatus.COMPLETE
                )
                checks.extend(
                    [
                        CheckRecord(
                            file_id=file.file_id,
                            check_id="identity",
                            executor_id="modelvet",
                            status=CheckStatus.COMPLETE,
                            result=CheckResult.NO_FINDINGS,
                            artifact_digest=manifest.manifest_digest,
                            details={"sha256": file.sha256},
                        ),
                        CheckRecord(
                            file_id=file.file_id,
                            check_id="classification",
                            executor_id="modelvet",
                            status=status,
                            result=CheckResult.NO_FINDINGS
                            if status == CheckStatus.COMPLETE
                            else CheckResult.UNKNOWN,
                            artifact_digest=manifest.manifest_digest,
                            reason=kind.reason,
                            details={
                                "format_class": kind.format_class.value,
                                "mismatch": kind.mismatch,
                            },
                        ),
                    ]
                )
                for inspector in (SafetensorsInspector(), ZipIndexInspector()):
                    if inspector.check_id in applicable_checks(kind.format_class):
                        checks.append(
                            normalize_inspection(file, manifest, inspector.inspect(file, snapshot))
                        )
                if kind.format_class == FileFormat.PYTHON_SOURCE:
                    checks.append(
                        CheckRecord(
                            file_id=file.file_id,
                            check_id="source:presence",
                            executor_id="modelvet",
                            status=CheckStatus.COMPLETE,
                            result=CheckResult.NO_FINDINGS,
                            artifact_digest=manifest.manifest_digest,
                            details={"source_present": True},
                        )
                    )
            metadata = MetadataReader().assess(snapshot, manifest)
            by_id = {file.file_id: file for file in manifest.files}
            checks.extend(
                normalize_inspection(by_id[key], manifest, inspection)
                for key, inspection in metadata.checks.items()
            )
            claims = [MetadataClaim(**asdict(claim)) for claim in metadata.claims]
            dependencies = DependencyReader().assess(snapshot, manifest)
            dependency_records = tuple(
                DependencyRecord(**asdict(record)) for record in dependencies.records
            )
            if dependencies.file_id is not None:
                checks.append(
                    normalize_inspection(by_id[dependencies.file_id], manifest, dependencies.check)
                )
                for record in dependencies.records:
                    value = f"{record.name}={record.version or 'UNKNOWN'}"
                    claim_id = hashlib.sha256(
                        f"DEPENDENCY\0{value}\0{record.source_ref}".encode()
                    ).hexdigest()
                    claims.append(
                        MetadataClaim(
                            claim_id=claim_id,
                            kind="DEPENDENCY",
                            value=value,
                            source_ref=record.source_ref,
                            source_file_id=dependencies.file_id,
                            source_sha256=record.source_sha256,
                        )
                    )
            executions: list[ToolExecution] = []
            findings: list[Finding] = []
            scanner_needed = any(
                "modelscan" in applicable_checks(kind.format_class) for kind in classes.values()
            )
            if scanner_needed:
                if request.scanner == "none":
                    raw = RawScannerExecution(
                        manifest.manifest_digest,
                        None,
                        "NOT_RUN",
                        reason="Scanner disabled by request.",
                    )
                else:
                    with tempfile.TemporaryDirectory(prefix="modelvet-work-") as directory:
                        raw = ModelScanAdapter().run(
                            snapshot, request.limits.timeout_s, Path(directory).resolve()
                        )
                executions, scanner_checks, findings = EvidenceNormalizer().normalize(
                    manifest, raw, classes
                )
                checks.extend(scanner_checks)
                for blob in (raw.stdout, raw.stderr, raw.report):
                    payloads[hashlib.sha256(blob).hexdigest()] = blob
                if raw.tool:
                    tools.append(ToolInfo(**asdict(raw.tool)))
            expectations = expectations_for(manifest, classes, frozenset(policy.mandatory_checks))

            def assess(
                current: list[CheckRecord],
            ) -> tuple[list[CoverageRecord], list[ConflictRecord], AdmissionDecision]:
                coverage = CoverageReconciler().reconcile(manifest, expectations, current)
                conflicts = ConflictDetector().detect(
                    claims, current, manifest, frozenset(policy.required_claims)
                )
                decision = AdmissionEvaluator().evaluate(
                    policy,
                    manifest,
                    coverage,
                    findings,
                    conflicts,
                    classifications=classes,
                    checks=current,
                    claims=claims,
                )
                return coverage, conflicts, decision

            assess(checks)
            checks = final_identity_checks(snapshot, manifest, checks)
            coverage, conflicts, decision = assess(checks)
            evidence = EvidenceBundle(
                tools=tuple(tools),
                checks=tuple(checks),
                claims=tuple(claims),
                dependencies=dependency_records,
                executions=tuple(executions),
                findings=tuple(findings),
                limitations=tuple(
                    sorted(
                        {
                            *dependencies.check.limitations,
                            *(s for c in checks for s in c.limitations),
                        }
                    )
                ),
            )
            run = RunMetadata(
                run_id=uuid.uuid4().hex,
                started_at=started,
                finished_at=datetime.now(UTC).isoformat(),
                modelvet_version=__version__,
                host_os_family="Darwin" if platform.system() == "Darwin" else "Linux",
                result_status="DEGRADED" if decision.state == "INSUFFICIENT" else "COMPLETE",
            )
            report = ReportBuilder().build(
                manifest,
                evidence,
                policy,
                decision,
                run,
                classifications=classes,
                coverage=coverage,
                conflicts=conflicts,
                raw_payloads=payloads,
                private_roots=(str(source.artifact_dir), str(snapshot.root), str(Path.home())),
            )
            snapshot_root = snapshot.root
        # Cleanup must succeed before a completed report is published.
        json_path, markdown_path = ReportWriter().write(
            report,
            source.output_dir,
            artifact_dir=source.artifact_dir,
            snapshot_dir=snapshot_root,
            raw_payloads=payloads,
            markdown=request.markdown,
        )
        return ScanOutcome(report, json_path, markdown_path, source.output_dir)
