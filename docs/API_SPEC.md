# Internal Python API specification — proposed

**No HTTP API planned.** These signatures are *design contracts* and may be refined via ADR; implementation is partial through PH-04; see PROGRESS for verified interfaces. Models in `evidence/models.py` own serialized data. All untrusted input and exceptions must be constrained at the adapter boundary.

## Input/identity and inventory

```python
class InputGate:
    def validate(self, artifact_dir: Path, output_dir: Path | None, limits: ScanLimits) -> ValidatedInput: ...
class Snapshotter:
    def create(self, source: ValidatedInput) -> Snapshot: ...  # context manager with private root
class InventoryService:
    def collect(self, snapshot: Snapshot) -> ArtifactManifest: ...
    def verify_unchanged(self, source: ValidatedInput, manifest: ArtifactManifest) -> bool: ...
class Classifier:
    def classify(self, file: ArtifactFile, snapshot: Snapshot) -> FileClassification: ...
```

**Errors:** `InvalidInput`, `BudgetExceeded`, `PathEscape`, `SnapshotChanged`, `IOFailure`. `collect` returns immutable manifest; never yields partial inventory as approval evidence. File descriptor-based checks where available; reject untrusted symlink races rather than assume `resolve()` suffices.

## Structural / metadata / dependencies

```python
class StructuralInspector(Protocol):
    check_id: str
    def applies_to(self, classification: FileClassification) -> bool: ...
    def inspect(self, file: ArtifactFile, snapshot: Snapshot) -> CheckRecord: ...
class MetadataReader:
    def collect_local_claims(self, snapshot: Snapshot, manifest: ArtifactManifest) -> list[MetadataClaim]: ...
class DependencyReader:
    def read_manifest(self, snapshot: Snapshot) -> list[DependencyRecord]: ...
```

Only parse declared JSON/text and bounded safetensors/ZIP metadata. No model imports, no `torch.load`. JSON duplicate-key detection should reject ambiguities in security-relevant configuration.

## Scanner adapter and normalization

```python
class ScannerAdapter(Protocol):
    @property
    def id(self) -> str: ...
    def probe(self) -> ToolInfo | ToolUnavailable: ...
    def run(self, snapshot: Snapshot, timeout_s: int, workdir: Path) -> RawScannerExecution: ...

class ModelScanAdapter:
    def probe(self) -> ToolInfo | ToolUnavailable: ...
    def run(self, snapshot: Snapshot, timeout_s: int, workdir: Path) -> RawScannerExecution: ...

class EvidenceNormalizer:
    def normalize(self, manifest: ArtifactManifest, raw: RawScannerExecution) -> tuple[list[ToolExecution], list[CheckRecord], list[Finding]]: ...
```

`RawScannerExecution` contains `argv`, sanitized environment fingerprint, scanner version, exit code, bounded stdout/stderr, output file path/raw bytes hash, timing and failure explanation. Invalid/oversized JSON → `FAILED`. Probe must record exact observed version. Map ModelScan CLI exit 0 no issues, 1 issues, 2 error, 3 unsupported input, 4 CLI usage error; **not** final ModelVet exits. Do not assume complete per-file coverage from exit 0; per-file evidence not provable → `INCONCLUSIVE`.

## Coverage / conflicts / policy

```python
class CoverageReconciler:
    def reconcile(self, manifest: ArtifactManifest, expectations: list[ExpectedCheck], evidence: list[CheckRecord]) -> list[CoverageRecord]: ...
class ConflictDetector:
    def detect(self, claims: list[MetadataClaim], checks: list[CheckRecord], manifest: ArtifactManifest) -> list[ConflictRecord]: ...
class PolicyValidator:
    def parse(self, toml_bytes: bytes) -> Policy: ...
class AdmissionEvaluator:
    def evaluate(self, policy: Policy, manifest: ArtifactManifest, coverage: list[CoverageRecord], findings: list[Finding], conflicts: list[ConflictRecord]) -> AdmissionDecision: ...
```

**Invariants:** no network in evaluator; same normalized inputs = identical decisions; every decision rule ID exists in policy/schema; only independently corroborated policy prohibition permits BLOCK before missing evidence; a conflicting critical claim cannot be resolved by a random ordering of scanners. `CoverageReconciler` never fills absent records with `COMPLETE`.

## Reports and CLI orchestration

```python
class ReportBuilder:
    def build(self, manifest: ArtifactManifest, evidence: EvidenceBundle, policy: Policy, decision: AdmissionDecision, run: RunMetadata) -> Report: ...
class ReportWriter:
    def write(self, report: Report, output_dir: Path) -> tuple[Path, Path]: ...
class ScanService:
    def run(self, request: ScanRequest) -> ScanOutcome: ...
```

`ScanOutcome` must always convey decision and output paths if reports are safely generated, and error classification otherwise. JSON schema validated before atomic save. `SemanticReportDigest` excludes observational run ID/time but includes policy version/hash, tool versions, snapshot identity, evidence and decision.

## Interface test matrix

| Interface | Contract tests | IDs |
|---|---|---|
| InputGate/Snapshotter | symlink, unreadable, mutation, budget, output overlap | T-INPUT-01, T-INV-01 |
| InventoryService | path normalization, deterministic digest, changed bytes | T-ID-01 |
| StructuralInspector | malformed ZIP/header, duplicate JSON keys, oversized metadata | T-STRUCT-01 |
| MetadataReader | missing and contradictory claims | T-META-01 |
| ModelScanAdapter | tool unavailable, 0/1/2/3/4, malformed stdout, timeout | T-SCAN-01 |
| EvidenceNormalizer | unknown statuses, raw hash, file-ID mismatch | T-EVID-01 |
| CoverageReconciler | skipped, partial, duplicate records, no-positive-proof | T-COV-01 |
| AdmissionEvaluator | all 4 outcomes, deterministic precedence, unknown mandatory | T-POLICY-01 |
| ReportWriter | schema, redaction, atomic-write failure | T-REPORT-01 |

## Evolution and versioning

Introduce `ScannerAdapterV2` only with schema migration and fixtures; do not silently change `run()` semantics. Keep scanner-specific JSON out of policy engine. New formats add classifier/inspector and applicability entries; new scanner adapters add contract fixtures. Avoid import cycles; `core` and `evidence` may not depend on CLI or reporting. No fake network route in MVP.

## PH-02 implementation checkpoint — 2026-10-20

InputGate/Snapshotter/InventoryService/Classifier exist; identity data are immutable internal dataclasses. Wire schemas are still scheduled for MV-011. A shared descriptor-based observer hashes source during post-scan rechecks without creating a second disk copy. `open_snapshot_file` contains reads and detects tested concurrent metadata changes; final full snapshot rehash is still required before admission. CLI scan is deliberately unavailable pending later orchestration.

## PH-03 implementation checkpoint — 2026-10-20

SafetensorsInspector/ZipIndexInspector expose `applies_to` and `inspect`, returning internal `Inspection` records until MV-011 normalizes wire evidence. MetadataReader `collect_local_claims` preserves the proposed list interface; `assess` additionally supplies per-file check status and missing kinds. DependencyReader `read_manifest` preserves its list interface; `assess` records check status and missing input. It reads only the fixed root `modelvet-environment.json` file within the snapshot. No installed model environment is inspected.

## MV-011 normalization refinement

`EvidenceNormalizer.normalize(manifest, raw, classifications=None)` returns typed executions/checks/findings. Supplying independently computed classifications is necessary to establish standalone-pickle context; omitting them remains inconclusive. Scanner paths are joined against canonical manifest paths without opening scanner-supplied paths. Invalid schema/identity/counts fail closed. `normalize_inspection` adapts bounded built-in outcomes. Resource proof is separately recorded and cannot be filled by scanner process success.

## PH-04 implementation checkpoint

Coverage expectations are materialized from independent applicability v2 via `expectations_for`; producers cannot erase required pairs by changing their own check lists. Reconcile preserves six disjoint terminal statuses and explicit mandatory IDs. `ConflictDetector.detect(..., required_claim_kinds=frozenset())` preserves opposing declarations and check/identity contradictions; claims are not legal findings. All serialized schema copies are packaged under `modelvet/schemas`. Next: policy evaluation; no admission outcome is currently produced by scan.

## PH-05 implemented evaluator/config contract

`PolicyValidator.parse(toml_bytes)` and `load_policy(path=None)` validate bounded data-only TOML. Explicit files replace the embedded default and never silently fall back. `AdmissionEvaluator.evaluate(policy, manifest, coverage, findings, conflicts, *, classifications, checks, claims)` requires owned classifications and normalized checks/claims to establish independent coverage and block proof; the coverage-only proposal was insufficient for that purpose. Inputs are not mutated. Decisions sort rule IDs/evidence/control IDs deterministically. See POLICY_SPEC for fact fields, supported prohibitions and control ownership. `policy validate` is implemented; full ScanService and ReportBuilder remain pending.

## Local static candidate implementation

application/scan.py owns ScanRequest/ScanOutcome/ScanService. ReportBuilder additionally requires independent classifications, coverage, conflicts, raw payloads and optional private roots. ReportWriter requires the artifact root and matching raw payload bytes. read_report validates stored schema/identity/coverage/reference/digest consistency without a fresh assessment or author authentication. Core/evidence do not import CLI/reports. Temporary cleanup succeeds before completed report publication; final identity recheck precedes final evaluation. Earlier pseudocode is the original proposal; implemented signatures and DATA_MODEL describe refinements.

## MV-020 offline advisory interface

`dependencies.advisories.AdvisoryReader.assess(dependencies, *, snapshot_path, as_of, artifact_digest, report_digest, max_age_days=7, required=True)` accepts immutable declaration/wire records and returns `AdvisoryAssessment`. `load_snapshot` reads and validates bounded OSV-envelope bytes with no network. `AdvisoryDocument.from_assessment` binds the output semantic digest and exit classification. Explicit version matching is conservative; unsupported semantics remain unresolved. This supplementary command does not modify ScanService, applicability v2 or the closed policy v1 vocabulary. If required operationally, callers must require success from both scan and advisories. Details: ADVISORY_SPEC.md.

## MV-022/023 development experiments

`benchmarks.corpus.load_manifest(path)` validates a bounded closed recipe manifest and re-establishes generator/file/artifact identity and stdlib method labels. `materialize(case, path)` exclusively creates private inert fixture bytes. `benchmarks.runner.run(manifest_path, output, repeats=2, timeout_s=120)` writes a fresh private pilot tree with result.json last as completion marker, returning `PilotResult`. `development_metrics(observations)` rejects duplicate/mismatched identities and separates eligibility, unavailability, partial states and policy blocks. No efficacy rates exist without reviewed positives. All pilot results are INCONCLUSIVE; no benchmark result can promote admission. External/human-reviewed holdout ingestion is not implemented.
