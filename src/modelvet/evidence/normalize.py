"""Bind scanner statements to independently computed file IDs and check statuses."""

import hashlib
import json
from pathlib import Path

from pydantic import ValidationError

from modelvet.core.errors import InvalidInput
from modelvet.core.json_data import strict_json
from modelvet.evidence.models import (
    CheckRecord,
    CheckResult,
    CheckStatus,
    ExecutionStatus,
    Finding,
    FindingVerification,
    Severity,
    ToolExecution,
)
from modelvet.evidence.modelscan_schema import ModelScanPayload
from modelvet.inventory.classify import FileClassification, FileFormat
from modelvet.inventory.discover import validate_relpath
from modelvet.inventory.identity import ArtifactFile, ArtifactManifest
from modelvet.scanners.base import RawScannerExecution
from modelvet.scanners.modelscan import MAX_RAW_REPORT, PINNED_MODELSCAN_VERSION
from modelvet.structural.base import Inspection


def normalize_inspection(
    file: ArtifactFile, manifest: ArtifactManifest, inspection: Inspection
) -> CheckRecord:
    status = CheckStatus(inspection.status)
    return CheckRecord(
        check_id=inspection.check_id,
        file_id=file.file_id,
        executor_id="modelvet",
        status=status,
        result=CheckResult.NO_FINDINGS if status == CheckStatus.COMPLETE else CheckResult.UNKNOWN,
        artifact_digest=manifest.manifest_digest,
        reason=inspection.reason,
        details=inspection.details,
        limitations=inspection.limitations,
    )


class EvidenceNormalizer:
    def normalize(
        self,
        manifest: ArtifactManifest,
        raw: RawScannerExecution,
        classifications: dict[str, FileClassification] | None = None,
    ) -> tuple[list[ToolExecution], list[CheckRecord], list[Finding]]:
        files = {file.relpath: file for file in manifest.files}
        classes = classifications or {}
        raw_digest = hashlib.sha256(raw.report).hexdigest() if raw.report else None
        raw_ref = "sha256:" + raw_digest if raw_digest else None
        findings: list[Finding] = []
        scanned: set[str] = set()
        nested: set[str] = set()
        skipped: set[str] = set()
        severity_unknown: set[str] = set()
        failure = raw.reason
        valid = False

        def bind(source: str) -> ArtifactFile:
            parent, separator, member = source.partition(":")
            validate_relpath(parent)
            if parent not in files:
                raise InvalidInput("Scanner references a file outside the independent manifest.")
            if separator:
                validate_relpath(member)
                nested.add(files[parent].file_id)
            return files[parent]

        try:
            if raw.artifact_digest != manifest.manifest_digest:
                raise InvalidInput("Scanner artifact digest mismatch.")
            if raw.tool is None or raw.tool.version != PINNED_MODELSCAN_VERSION:
                raise InvalidInput("Scanner tool/version unavailable.")
            strict_json(raw.report, MAX_RAW_REPORT)
            payload = ModelScanPayload.model_validate_json(raw.report)
            summary = payload.summary
            expected_root = raw.argv[raw.argv.index("-p") + 1]
            if (
                not Path(expected_root).is_absolute()
                or summary.input_path != expected_root
                or summary.absolute_path != expected_root
                or summary.modelscan_version != raw.tool.version
            ):
                raise InvalidInput("Scanner context or version does not match invocation.")
            for path in summary.scanned.scanned_files:
                file = bind(path)
                scanned.add(file.file_id)
            for skipped_file in summary.skipped.skipped_files:
                skipped.add(bind(skipped_file.source).file_id)
            for index, issue in enumerate(payload.issues):
                file = bind(issue.source)
                severity = (
                    Severity(issue.severity) if issue.severity in Severity else Severity.UNKNOWN
                )
                if severity == Severity.UNKNOWN:
                    severity_unknown.add(file.file_id)
                fingerprint = hashlib.sha256(
                    json.dumps(
                        [file.file_id, issue.model_dump(mode="json")], sort_keys=True
                    ).encode()
                ).hexdigest()
                findings.append(
                    Finding(
                        finding_id=fingerprint,
                        file_id=file.file_id,
                        check_id="modelscan",
                        category="SCANNER_REPORTED_OPERATOR",
                        severity=severity,
                        verification_state=FindingVerification.REPORTED,
                        source_ref=f"{raw_ref}#issues/{index}",
                        description=issue.description,
                    )
                )
            if (
                payload.errors
                or raw.exit_code not in (0, 1)
                or (raw.exit_code == 0 and payload.issues)
                or (raw.exit_code == 1 and not payload.issues)
            ):
                raise InvalidInput("Scanner errors or exit/result contradiction.")
            valid = True
        except (InvalidInput, ValidationError, ValueError, IndexError):
            failure = failure or "Scanner schema, identity or completeness proof invalid."

        checks: list[CheckRecord] = []
        files_with_findings = {finding.file_id for finding in findings}
        for file in manifest.files:
            status = CheckStatus(raw.status)
            reason = failure
            if raw.status == "COMPLETE":
                status = CheckStatus.FAILED if not valid else CheckStatus.INCONCLUSIVE
                classification = classes.get(file.file_id)
                if valid and file.file_id in skipped:
                    status = CheckStatus.SKIPPED
                    reason = "Scanner explicitly skipped this file."
                if valid and file.file_id in scanned:
                    if file.file_id in skipped or file.file_id in severity_unknown:
                        status = CheckStatus.INCONCLUSIVE
                        reason = "Contradictory coverage or unknown scanner severity."
                    elif (
                        classification is not None
                        and classification.format_class == FileFormat.PICKLE_LIKE
                        and file.file_id not in nested
                    ):
                        status = CheckStatus.COMPLETE
                        reason = None
                    else:
                        status = CheckStatus.INCONCLUSIVE
                        reason = "Format context or archive-member completeness is unproven."
                if valid and file.file_id not in scanned | skipped:
                    reason = "No positive per-file scanner proof."
            has_findings = file.file_id in files_with_findings
            checks.append(
                CheckRecord(
                    check_id="modelscan",
                    file_id=file.file_id,
                    executor_id="modelscan",
                    status=status,
                    result=(CheckResult.FINDINGS if has_findings else CheckResult.NO_FINDINGS)
                    if status == CheckStatus.COMPLETE
                    else CheckResult.UNKNOWN,
                    artifact_digest=manifest.manifest_digest,
                    raw_ref=raw_ref,
                    reason=reason,
                    error_code=(
                        "SCANNER_IDENTITY_MISMATCH"
                        if raw.artifact_digest != manifest.manifest_digest
                        else "SCANNER_COVERAGE_CONFLICT"
                        if file.file_id in scanned & skipped
                        else "INVALID_SCANNER_EVIDENCE"
                        if not valid
                        else None
                    ),
                    details={"contradictory_coverage": file.file_id in scanned & skipped},
                    limitations=raw.limitations,
                )
            )
            if classification := classes.get(file.file_id):
                if "modelscan" in classification.check_ids:
                    resources = CheckStatus.COMPLETE
                    if raw.tool is None:
                        resources = CheckStatus.NOT_RUN
                    elif any("memory is not OS-bounded" in item for item in raw.limitations):
                        resources = CheckStatus.UNSUPPORTED
                    elif not raw.environment_digest or raw.reason in {"TIMEOUT", "OUTPUT_LIMIT"}:
                        resources = CheckStatus.FAILED
                    checks.append(
                        CheckRecord(
                            check_id="scanner:resources",
                            file_id=file.file_id,
                            executor_id="modelscan",
                            status=resources,
                            result=CheckResult.NO_FINDINGS
                            if resources == CheckStatus.COMPLETE
                            else CheckResult.UNKNOWN,
                            artifact_digest=manifest.manifest_digest,
                            reason=None
                            if resources == CheckStatus.COMPLETE
                            else "Scanner resource contract unresolved.",
                            limitations=raw.limitations,
                        )
                    )
        execution_states: dict[str, ExecutionStatus] = {
            "UNSUPPORTED": "INCONCLUSIVE",
            "COMPLETE": "COMPLETE",
            "FAILED": "FAILED",
            "NOT_RUN": "NOT_RUN",
        }
        execution_status = execution_states[raw.status]
        if raw.status == "COMPLETE" and not valid:
            execution_status = "FAILED"
        execution = ToolExecution(
            execution_id="modelscan:" + manifest.manifest_digest.split(":")[1],
            tool_id="modelscan",
            status=execution_status,
            artifact_digest=raw.artifact_digest,
            exit_code=raw.exit_code,
            started_at=raw.started_at,
            ended_at=raw.ended_at,
            stdout_digest=hashlib.sha256(raw.stdout).hexdigest(),
            stderr_digest=hashlib.sha256(raw.stderr).hexdigest(),
            raw_report_digest=raw_digest,
            environment_digest=raw.environment_digest,
            reason=failure,
            limitations=raw.limitations,
        )
        return [execution], checks, findings
