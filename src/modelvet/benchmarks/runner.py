"""Run closed inert development recipes with existing process/report boundaries."""

import argparse
import hashlib
import json
import os
import platform
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Never

from pydantic import Field, JsonValue, model_validator

from modelvet import __version__
from modelvet.application.scan import ScanRequest, ScanService
from modelvet.benchmarks.corpus import load_manifest, materialize
from modelvet.benchmarks.metrics import Observation, development_metrics
from modelvet.core.errors import InvalidInput
from modelvet.core.limits import ScanLimits
from modelvet.core.snapshot import Snapshotter
from modelvet.evidence.models import ArtifactDigest, WireModel
from modelvet.evidence.normalize import EvidenceNormalizer
from modelvet.inventory.classify import Classifier
from modelvet.inventory.gate import InputGate, absolute_path
from modelvet.inventory.identity import InventoryService
from modelvet.reports.writer import _atomic, _directory
from modelvet.scanners.modelscan import ModelScanAdapter


class PilotResult(WireModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    study_status: Literal["INCONCLUSIVE"] = "INCONCLUSIVE"
    corpus_digest: ArtifactDigest
    platform: str
    observed_at: str
    repeats: int = Field(ge=1, le=3)
    fixture_ids: tuple[str, ...]
    observations: tuple[Observation, ...]
    metrics: dict[str, JsonValue]
    alternatives: dict[str, str] = Field(
        default_factory=lambda: {
            "PickleBall": "NOT_RUN: no reviewed adapter configured; not counted as failure.",
            "Layerfault": "NOT_RUN: no reviewed adapter configured; not counted as failure.",
            "commercial_tools": "NOT_RUN: no access/configuration supplied; no comparison made.",
        }
    )
    limitations: tuple[str, ...] = (
        "Synthetic development pilot; independent review and hidden holdout are pending.",
        "ModelScan uses the conservative pinned adapter interpretation; raw evidence retained.",
        "Admission and scanner assessment differ; no detection superiority inference.",
        "Darwin required memory enforcement is unavailable; subprocesses are not containment.",
        "Distinct pipelines/probes are timed; peak RSS and comparative overhead are unmeasured.",
        "No loader execution, malware efficacy, legal clearance or public release validation.",
    )

    @model_validator(mode="after")
    def consistent_metrics(self) -> "PilotResult":
        expected = {
            (f, t, r)
            for f in self.fixture_ids
            for t in ("modelvet", "modelscan")
            for r in range(1, self.repeats + 1)
        }
        actual = {(o.fixture_id, o.tool_id, o.repeat_id) for o in self.observations}
        if (
            not self.fixture_ids
            or len(set(self.fixture_ids)) != len(self.fixture_ids)
            or actual != expected
        ):
            raise ValueError("Every fixture/tool/repeat must be accounted for.")
        if self.metrics != development_metrics(self.observations):
            raise ValueError("Pilot metrics disagree with observations.")
        return self


def run(manifest_path: Path, output: Path, repeats: int = 2, timeout_s: int = 120) -> PilotResult:
    if type(repeats) is not int or not 1 <= repeats <= 3:
        raise InvalidInput("Benchmark repeats must be 1–3.")
    limits = ScanLimits(timeout_s=timeout_s)
    manifest = load_manifest(manifest_path)
    # Freeze the validated manifest representation, not a later second path read.
    corpus_digest = "sha256:" + hashlib.sha256(manifest.model_dump_json().encode()).hexdigest()
    selected = absolute_path(output)
    try:
        parent_fd = _directory(selected.parent)
    except OSError as exc:
        raise InvalidInput("Benchmark output parent is unsafe.") from exc
    try:
        os.mkdir(selected.name, 0o700, dir_fd=parent_fd)
        output_fd = os.open(
            selected.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd
        )
    except OSError as exc:
        raise InvalidInput("Benchmark output must be a new safe directory.") from exc
    finally:
        os.close(parent_fd)
    observations = []
    emitted: set[str] = set()
    raw_bytes = 0
    try:
        for case in manifest.cases:
            for repeat in range(1, repeats + 1):
                with tempfile.TemporaryDirectory(prefix="modelvet-bench-") as directory:
                    temporary = Path(directory).resolve()
                    artifact = temporary / "artifact"
                    materialize(case, artifact)
                    if case.baseline_eligibility == "STANDALONE_PICKLE":
                        source = InputGate().validate(artifact, selected / "reports", limits)
                        started = time.perf_counter()
                        with Snapshotter().create(source) as snapshot:
                            identity = InventoryService().collect(snapshot)
                            if identity.manifest_digest != case.artifact_digest:
                                raise InvalidInput("Benchmark artifact differs from frozen corpus.")
                            classes = {
                                f.file_id: Classifier().classify(f, snapshot)
                                for f in identity.files
                            }
                            raw = ModelScanAdapter().run(snapshot, timeout_s, temporary)
                            _, checks, _ = EvidenceNormalizer().normalize(identity, raw, classes)
                            target = next(
                                f.file_id for f in identity.files if f.relpath == "weights.pkl"
                            )
                            check = next(
                                c
                                for c in checks
                                if c.file_id == target and c.check_id == "modelscan"
                            )
                        references = []
                        for blob in (raw.stdout, raw.stderr, raw.report):
                            digest = hashlib.sha256(blob).hexdigest()
                            references.append("sha256:" + digest)
                            if digest not in emitted:
                                raw_bytes += len(blob)
                                if raw_bytes > 32 * 1024 * 1024:
                                    raise InvalidInput("Benchmark raw evidence budget exceeded.")
                                _atomic(output_fd, "raw-" + digest + ".bin", blob)
                                emitted.add(digest)
                        metadata = {
                            "argv": [
                                "<pinned-modelscan>",
                                "-p",
                                "<snapshot>",
                                "--reporting-format",
                                "json",
                                "--show-skipped",
                                "--output-file",
                                "<private-json>",
                            ],
                            "status": raw.status,
                            "exit_code": raw.exit_code,
                            "tool_version": raw.tool.version if raw.tool else None,
                            "binary_sha256": raw.tool.binary_sha256 if raw.tool else None,
                            "artifact_digest": raw.artifact_digest,
                            "started_at": raw.started_at,
                            "ended_at": raw.ended_at,
                            "environment_digest": raw.environment_digest,
                            "raw_refs": references,
                            "limitations": list(raw.limitations),
                        }
                        metadata_bytes = json.dumps(metadata, sort_keys=True).encode()
                        name = f"baseline-{case.fixture_id}-{repeat}.json"
                        _atomic(output_fd, name, metadata_bytes)
                        baseline = Observation(
                            fixture_id=case.fixture_id,
                            artifact_digest=case.artifact_digest,
                            tool_id="modelscan",
                            tool_version=raw.tool.version if raw.tool else None,
                            repeat_id=repeat,
                            eligibility="SUPPORTED_CONTEXT",
                            outcome="UNAVAILABLE"
                            if raw.tool is None
                            else (
                                "UNRESOLVED"
                                if check.status != "COMPLETE"
                                else (
                                    "REPORTED_FINDINGS"
                                    if check.result == "FINDINGS"
                                    else "COMPLETE_NO_FINDINGS"
                                )
                            ),
                            wall_s=time.perf_counter() - started,
                            evidence_ref=name,
                            raw_refs=tuple(references),
                            reason=check.reason,
                        )
                    else:
                        baseline = Observation(
                            fixture_id=case.fixture_id,
                            artifact_digest=case.artifact_digest,
                            tool_id="modelscan",
                            tool_version=None,
                            repeat_id=repeat,
                            eligibility="NOT_APPLICABLE",
                            outcome="NOT_APPLICABLE",
                            wall_s=0.0,
                            reason="Outside predeclared standalone-pickle comparison context.",
                        )
                    observations.append(baseline)
                    started = time.perf_counter()
                    assessment = ScanService().run(
                        ScanRequest(
                            artifact,
                            selected / "reports",
                            limits=limits,
                        )
                    )
                    report = assessment.report
                    if report.manifest_digest != case.artifact_digest:
                        raise InvalidInput(
                            "ModelVet report does not bind frozen benchmark identity."
                        )
                    observations.append(
                        Observation(
                            fixture_id=case.fixture_id,
                            artifact_digest=case.artifact_digest,
                            tool_id="modelvet",
                            tool_version=__version__,
                            repeat_id=repeat,
                            eligibility="SUPPORTED_CONTEXT",
                            outcome=(
                                "REPORTED_FINDINGS"
                                if report.findings
                                else (
                                    "POLICY_BLOCK"
                                    if report.decision.state == "BLOCK"
                                    else (
                                        "UNRESOLVED"
                                        if report.decision.state == "INSUFFICIENT"
                                        else "COMPLETE_NO_FINDINGS"
                                    )
                                )
                            ),
                            wall_s=time.perf_counter() - started,
                            decision=report.decision.state,
                            evidence_ref=str(assessment.json_path.relative_to(selected)),
                        )
                    )
        result = PilotResult(
            corpus_digest=corpus_digest,
            platform=platform.system(),
            observed_at=datetime.now(UTC).isoformat(),
            repeats=repeats,
            fixture_ids=tuple(c.fixture_id for c in manifest.cases),
            observations=tuple(observations),
            metrics=development_metrics(tuple(observations)),
        )
        # Complete result is the final publication marker. Partial evidence may remain on failure.
        _atomic(output_fd, "result.json", result.model_dump_json(indent=2).encode())
        os.fsync(output_fd)
        return result
    finally:
        os.close(output_fd)


class PilotArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        self.exit(40, "Invalid benchmark arguments; use --help.\n")


def main() -> None:
    parser = PilotArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--timeout-sec", type=int, default=120)
    args = parser.parse_args()
    try:
        result = run(args.manifest, args.out, args.repeats, args.timeout_sec)
        print(
            json.dumps(
                {
                    "study_status": result.study_status,
                    "observations": len(result.observations),
                    "result": "<output>/result.json",
                }
            )
        )
        raise SystemExit(30)
    except InvalidInput as exc:
        parser.exit(40, f"Invalid benchmark input: {exc}\n")
    except KeyboardInterrupt:
        parser.exit(130, "Benchmark interrupted; no result finalized.\n")
    except Exception:
        parser.exit(
            50, "Benchmark failed before completion; private partial evidence may remain.\n"
        )


if __name__ == "__main__":
    main()
