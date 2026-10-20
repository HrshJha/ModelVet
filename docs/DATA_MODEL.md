# Data model and wire schema — v1 proposal

**Status:** evidence/coverage/conflict/policy/decision/report v1 records implemented for the local static candidate. All JSON example values below illustrative. `schema_version: "1.0.0"`; semantic versioning: additive optional fields in minor versions, changes in required fields/enums/meaning are major. Unknown `schema_version` major must fail validation; unknown enum is not assumed clean. All serialized timestamps use UTC RFC3339; creation times are **not** included in semantic decision digest. JSON uses UTF-8, sorted canonical keys for hashing, no NaN/Infinity. Unknown top-level keys are forbidden in implemented v1; no extensions container is accepted.

## Entity contracts

| Entity / responsible module | Required fields (types) | Optional fields | Invariants / relationships | Missing data |
|---|---|---|---|---|
| `ArtifactIdentity` inventory | `manifest_digest:str`, `hash_algorithm:'sha256'`, `file_count:int`, `total_bytes:int` | `declared_repo`, `declared_revision` | computed from canonical relative paths, file content digests, sizes, format version; names/revisions are claims | missing revision is `null`, not identity |
| `ArtifactFile` inventory | `file_id:str`, `relpath:str`, `size:int`, `sha256:str`, `format_class:enum` | `signature`, `declared_role` | `file_id = sha256(relpath + NUL + sha256)`; no duplicate normalized path; never follow symlinks | class may be `UNKNOWN`, never omitted |
| `ToolInfo` adapter | `tool_id:str`, `version:str`, `source:str` | `binary_sha256` | tool version is observed/pinned; unknown version invalid if tool mandatory | `null` only when not-run, with reason |
| `ToolExecution` scanner | `execution_id`, `tool_id`, `status`, `started_at`, `artifact_digest` | `ended_at`, `exit_code`, `stdout_digest`, `stderr_digest`, `timeout_s`, `limitation` | `status` in COMPLETE/FAILED/NOT_RUN/INCONCLUSIVE; raw digest and raw stored separately | no report != no findings |
| `CheckRecord` evidence | `check_id`, `file_id`, `executor_id`, `status`, `result`, `artifact_digest`, `normalizer_version` | `raw_ref`, `started_at`, `ended_at`, `error_code`, `reason` | one check result per `(executor_id,file_id,check_id)` unless retry indexed; `COMPLETE` + `NO_FINDINGS` only with actual execution proof | `UNKNOWN` for noncomplete |
| `Finding` evidence | `finding_id`, `file_id`, `check_id`, `category`, `severity`, `verification_state`, `source_ref` | `description`, `location`, `related_cve`, `rule_id` | stable normalized ID; severity not policy decision; verification `REPORTED/CORROBORATED/DISPUTED` | unknown severity explicit `UNKNOWN` |
| `CoverageRecord` coverage | `file_id`, `expected_check_ids:list[str]`, `completed_check_ids`, `skipped_check_ids`, `failed_check_ids`, `unsupported_check_ids`, `inconclusive_check_ids`, `unresolved_reasons` | `nonapplicable_check_ids` | disjoint check status buckets; union covers expected applicable set; every required check accounted for | missing tool response => unresolved |
| `MetadataClaim` metadata | `claim_id`, `kind:LICENSE/PROVENANCE/DEPENDENCY`, `value:str`, `source_ref`, `confidence:DECLARED/INFERRED/HUMAN_REVIEWED` | `source_line`, `declared_repo` | only assert source says X, not X legally verified | absent claim recorded explicitly |
| `ConflictRecord` coverage | `conflict_id`, `type`, `claim_ids`, `decision_relevant:bool`, `reason` | `resolution_ref` | conflicting assertions preserved; resolver must cite evidence | unresolved remains unresolved |
| `DependencyRecord` dependencies | `name`, `ecosystem`, `version`, `source_ref`, `status` | `purl`, `advisories:list` | no vulnerability assertion without matching affected version + source | unknown version = inconclusive |
| `Policy` policies | `policy_id`, `policy_version`, `mandatory_checks`, `prohibitions`, `control_rules`, `applicability_version` | `required_claims`, `advisory_max_age_days` | TOML parsed and typed; semantic hash derived from normalized config | unknown keys invalid |
| `AdmissionDecision` policies | `state:enum`, `rule_ids:list[str]`, `reason`, `evidence_refs` | `required_controls:list[str]` | APPROVE only all required complete; CONTROLS include controls; BLOCK corroborated policy rule | no null state |
| `RunMetadata` reports | `run_id`, `started_at`, `finished_at`, `modelvet_version`, `host_os_family`, `result_status` | `tool_versions`, `config_digest` | operation metadata excluded from semantic digest | host OS family may be generalized for privacy |
| `Report` reports | `schema_version`, `artifact`, `run`, `policy`, `files`, `checks`, `coverage`, `findings`, `claims`, `conflicts`, `decision`, `limitations`, `semantic_digest` | `dependencies`, `tools`, `extensions` | every referenced file/check exists; no dangling refs; decision refers to rule IDs | use [] for known empty, null only unknown fields |
| `LoaderContext` (P2) verification | `runtime`, `runtime_version`, `framework`, `framework_version`, `entrypoint`, `flags`, `artifact_digest` | `environment_digest`, `isolation_profile` | exact context/hash; not valid without sandbox proof | absent in MVP |
| `VerificationRun` (P2) verification | `run_id`, `loader_context`, `isolation_status`, `observation_refs` | `guest_image_digest`, `syscall_trace_digest` | separate `access`, `attempted_execution`, `observed_execution`, `inferred` classes | `INCONCLUSIVE` on instrumentation miss |

## Enumerations

- `DecisionState = APPROVE | CONTROLS | BLOCK | INSUFFICIENT`.
- `CheckStatus = COMPLETE | SKIPPED | FAILED | UNSUPPORTED | INCONCLUSIVE | NOT_RUN`.
- `CheckResult = FINDINGS | NO_FINDINGS | UNKNOWN`.
- `FindingVerification = REPORTED | CORROBORATED | DISPUTED`.
- `Severity = CRITICAL | HIGH | MEDIUM | LOW | INFO | UNKNOWN`; scanner severity maps documented and versioned, no implicit policy decision.
- `FileFormat = SAFETENSORS | PICKLE_LIKE | PYTORCH_ZIP | ZIP_OTHER | JSON | MARKDOWN | TEXT | PYTHON_SOURCE | BINARY_UNKNOWN | UNKNOWN`.

## Stable identity algorithm (proposed `manifest-v1`)

1. `lstat` every path (no symlink follow), normalize path separators to `/`, require NFC Unicode, and reject duplicate canonical paths/case collision only where applicable; reject `.`/`..`, NUL and absolute member names.
2. `sha256` raw file bytes via bounded streaming, record exact integer byte size.
3. Canonical ordered manifest lines: `relative_path + NUL + decimal_size + NUL + lowercase_sha256 + LF` sorted by UTF-8 encoded path bytes. Prefix canonical manifest with `modelvet-manifest-v1\n`; `manifest_digest=sha256(prefix + entries)`.
4. File IDs are deterministic domain-separated hashes: `sha256(b'modelvet-file-v1\0'+utf8_relpath+b'\0'+bytes.fromhex(file_sha256))`.
5. Snapshot and original artifact double-check is a **best effort mutation detector**, not a cryptographically atomic filesystem snapshot guarantee. Changes found post-scan set mandatory `identity` FAILED and decision INSUFFICIENT; no stale APPROVE.

## Coverage invariant and completeness proof

For each `f` in inventory and `c` in applicable checks, materialize `(f,c,requirement_level)` before scans. Every pair must end in exactly one terminal status. `complete(f,c)` iff scanner actually assessed that file/check and a verified status/result maps back to snapshot hash. Scanner process exit 0 alone does not show that a particular file was inspected. If adapter JSON cannot support positive per-file proof, mark `INCONCLUSIVE` rather than fill COMPLETE. `CoverageRecord` is an *assessment-completeness record*, not a malware-free certificate.

### Illustrative wire sample, NOT an actual scan

```json
{
  "schema_version": "1.0.0",
  "artifact": {"manifest_digest": "sha256:exampleonly", "hash_algorithm": "sha256", "file_count": 1, "total_bytes": 128},
  "run": {"run_id": "illustrative", "started_at": "2026-10-20T00:00:00Z", "finished_at": "2026-10-20T00:00:01Z", "modelvet_version": "planned", "host_os_family": "linux", "result_status": "COMPLETE"},
  "policy": {"policy_id": "default", "policy_version": "1", "mandatory_checks": ["modelscan"], "prohibitions": [], "control_rules": [], "applicability_version": "1"},
  "files": [{"file_id": "example-file", "relpath": "weights.pt", "size": 128, "sha256": "example", "format_class": "PYTORCH_ZIP"}],
  "checks": [{"check_id": "modelscan", "file_id": "example-file", "executor_id": "modelscan", "status": "SKIPPED", "result": "UNKNOWN", "artifact_digest": "sha256:exampleonly", "normalizer_version": "1", "reason": "Tool did not inspect member"}],
  "coverage": [{"file_id": "example-file", "expected_check_ids": ["modelscan"], "completed_check_ids": [], "skipped_check_ids": ["modelscan"], "failed_check_ids": [], "unsupported_check_ids": [], "inconclusive_check_ids": [], "unresolved_reasons": ["required check skipped"]}],
  "findings": [], "claims": [], "conflicts": [],
  "decision": {"state": "INSUFFICIENT", "rule_ids": ["MISSING-MANDATORY"], "reason": "Required coverage incomplete", "evidence_refs": ["example-file"]},
  "limitations": ["No model loading"], "semantic_digest": "sha256:illustrative"
}
```

## Conflict and precedence examples

- `README.md: Apache-2.0` and `config.json: CC-BY-NC`: preserve both `MetadataClaim`s and an unresolved `LICENSE` conflict. No automated legal verdict. If policy requires clarity, `INSUFFICIENT`.
- `scanner says NO_FINDINGS` but `ToolExecution FAILED`: normalize result `UNKNOWN`, record conflict, `INSUFFICIENT` if required.
- P2 `observed_execution` is not inferred merely from a static `GLOBAL` pickle opcode; do not collapse observation into prediction.

## Storage / privacy / migrations

Report JSON and Markdown in a user-designated report directory, raw reports in a restricted subdirectory with hashes, snapshot in a temp directory deleted. Do not store original sensitive input bytes in reports. Provide JSON Schema generated from Pydantic after implementation; include pinned schema copies and golden fixtures in tests. Migration v1→v2 requires explicit compatibility tests; do not silently reinterpret old status values.

## Implemented classifier applicability v1 — MV-006

All files require `identity` and `classification`. Safetensors additionally uses `structural:safetensors`; ZIP/PyTorch ZIP uses `structural:zip` and `modelscan`; pickle-like uses `modelscan`; JSON/Markdown/text uses `metadata:local`; repository Python files use `source:presence`. Unknown formats retain classification uncertainty; extension/signature disagreements remain explicit. These are applicability expectations, not completed coverage. Policy and normalized evidence are not implemented at this checkpoint.

## Explicit environment input v1 — MV-009

A user may place `modelvet-environment.json` at artifact root, so its bytes are included in identity. Envelope: `{"schema_version":"1.0.0","dependencies":[{"name":"torch","ecosystem":"PyPI","version":"2.6.0"}]}`. Unknown keys and malformed envelopes fail. Only the documented conservative subset of exact PyPI version strings is recognized; missing, ranged, unsupported-ecosystem or duplicate/conflicting pins are INCONCLUSIVE declarations, never a no-vulnerability assertion. Absence is explicit and no host environment is guessed. When present, this file additionally expects `dependencies:declared`; the policy layer will determine mandatory coverage.

## PH-04 evidence implementation (MV-011)

Strict Pydantic v1 evidence schema is exported at `schemas/evidence-v1.json` and packaged under `modelvet/schemas/`. Known result is allowed only on COMPLETE checks; scanner findings remain REPORTED. Source identity, raw hashes and process/tool statuses remain separate. Normalized execution times require UTC RFC3339; vendor timestamps remain untrusted raw data. Applicability v2 adds `scanner:resources` to serialized-model scanner checks, so the documented Darwin memory-limit gap is a mandatory unresolved check. Named standalone-pickle proof is supported for ModelScan 0.8.8; missing context or archive member completeness is INCONCLUSIVE. No admission decision is implemented yet.

## MV-012 coverage wire clarification

CoverageRecord additionally serializes `mandatory_check_ids` and `not_run_check_ids` so requirement level and NOT_RUN are not lost. The disjoint terminal buckets exactly partition expected applicable IDs; missing proof is INCONCLUSIVE. Duplicate observations remain unresolved. `mandatory_unresolved` is derived from required IDs minus completed IDs, not a clean percentage. Schema: `schemas/coverage-v1.json`. These additions resolve omissions in the draft table before release.

## MV-013 conflict wire clarification

ConflictRecord includes `check_refs` (semantic check hashes) and optional `subject`, alongside claim IDs, relevance and reason. At least one source reference is required. Distinct provenance fields are compared separately; differing license declarations remain sourced statements and are relevant only when the policy requires that kind. Identity/status contradictions are always relevant. No automatic legal resolution or human exception is applied. Schema: `schemas/conflict-v1.json`.

## PH-05 policy/decision refinement

`Policy` includes explicit `optional_checks` covering the remainder of the fixed applicability-v2 registry, declared `controls`, rules and optional required claim kinds. `AdmissionDecision.required_controls` contains `{control_id, owner}` records; this refines the earlier proposed string list to satisfy the PRD owner requirement. Policy/decision JSON schemas are packaged with the three PH-04 schemas. Cross-field validation remains normative in addition to JSON schema shape constraints. See POLICY_SPEC for the closed vocabulary, stable effective-policy hash and proof requirements.

## Implemented report v1 contract

Report v1 contains typed artifact/file identity, policy/effective digest, tools/executions/checks, findings, coverage, claims/dependencies/conflicts, decision, limitations, private raw evidence metadata, run metadata and source-reference index. The index maps original semantic IDs to validated JSON pointers, preserving original references when text is redacted. Exact filenames and operator policy/owners remain potentially sensitive audit inputs. Six schemas are packaged, with additional cross-field validators.

Semantic projection excludes run metadata and observational raw/log/environment digests/attachment records; raw-backed finding pointers use a stable logical issue pointer. It retains artifact/policy/tool/normalized evidence/decision semantics. Report bounds are 32 MiB/2,000,000 tokens; artifact JSON retains 100,000 tokens. A digest is not authentication. Final source/snapshot drift fails identity and independent ban proof before publication.

## MV-020 supplementary advisory v1

The separate `advisories-v1.json` schema defines `AdvisoryDocument`: assessment plus validated semantic digest/exit code. Assessment binds artifact identity, original report semantic digest, snapshot byte digest, source-claim hash, explicit evaluation/generation time, age/requirement parameters and per-dependency status/result/OSV pointer records. It carries `admission_recomputed=false` and no AdmissionDecision. Original report v1 shape and policy applicability v2 remain unchanged. Matching and unresolved semantics are defined in ADVISORY_SPEC.md; no advisories are silently inserted into existing report JSON.

## MV-022/023 development corpus and pilot records

`benchmark-corpus-v1.json` freezes ten closed inert recipe identities, per-file hashes/sizes, MIT provenance, baseline input-context eligibility and method-checked development labels. It permits neither independent-review promotion nor hidden-holdout claims. `benchmark-run-v1.json` binds canonical validated corpus digest, fixture IDs, tool/version/repeat/artifact observations, raw/evidence references, actual wall durations and derived counts. Peak RSS remains null. Completed run records account for every fixture/tool/repeat and recompute metrics for consistency. Study status is INCONCLUSIVE; efficacy/error rates and confidence intervals remain null without independent adjudication. Context/whole-result hashes and source/runtime observations are retained in verification/MV-023/experiment.json.
