# ModelVet — Product Requirements Document

| Field | Value |
|---|---|
| Document version | `0.1.0-draft` |
| Status | **PROPOSED requirements; local static candidate through PH-10; hosted Ubuntu/macOS validation passed; public release pending** |
| Updated | 2026-10-20 |
| Development stage | P0 local workflow implemented; Ubuntu 24.04/macOS 15 Intel hosted gates passed; public release pending review |
| Product | Open-source local AI model artifact security and admission verification |
| Authority | Primary source of truth for requirements; `docs/DECISIONS.md` for why |
| Scope | Local artifact assessment MVP; isolated loading is a gated future experiment |

## 1. Executive summary

ModelVet is to be a local Python CLI that inventories an untrusted model directory, assesses bounded local formats and local claims, runs an optional but policy-required existing scanner, **independently accounts for required-check coverage**, and produces an auditable policy decision. It does not promise to certify model safety or determine license legality. Its experimental differentiator is whether independently recorded file coverage and, later, loader-context evidence identify materially missed assessments. This is a **research hypothesis**, not a demonstrated competitive advantage.

## 2. Problem, users and evidence

**Current workflow:** a developer downloads model files, reads an HF model card, runs a scanner, and loads them. A scanner may skip unreadable content or fail to model the exact loading path. Repository license fields may conflict with embedded declarations; the loader and dependencies may be vulnerable. A no-findings result does not imply all relevant checks were complete. This matters for developers, AppSec reviewers, and ML platform operators bringing third-party code and weights near credentials or deployment infrastructure.

**Grounded failure:** Protect AI ModelScan issue #354 describes a fail-open archive traversal discrepancy as reported by a researcher, not an independently re-executed finding here. Its current documented CLI exit behavior distinguishes tool errors and no supported files. Hugging Face recommends safetensors and pinned revisions; PyTorch says restricted weights-only loading still does not rule out DoS/memory risks. See `docs/RESEARCH_REFERENCES.md`.

**Unproven:** that ModelVet detects more vulnerabilities than JFrog, Protect AI, Layerfault or any other competitor; that customers will pay for the precise coverage distinction; that a deterministic static pass guarantees loader safety.

## 3. Goals and explicit non-goals

**Release goals:** stable local identity; zero silent promotions of mandatory failed checks; attributable per-file evidence; deterministic policy evaluation; safe bounded structural parsers; output fit for humans and CI; reproducible benign/adversarial *non-executable* tests; benchmark capable of disproving incremental advantage.

**Not in MVP:** universal malware detection, malicious model execution, remote Hub downloads, hosted service, web UI, database server, Kubernetes, model poisoning/backdoor inference evaluation, real-time feed polling, an LLM judge, automatic legal clearance, team billing or startup metrics. P1 adds optional offline advisory enrichment and external benchmark. P2 may add *explicitly authorized, isolated* loader testing after a security gate; P2 is not part of the first release.

## 4. Target user journeys

| Scenario | User supplies | Expected path | Degraded/error behavior |
|---|---|---|---|
| Local model preflight | Directory, policy | Inventory → evidence → policy → reports | Missing files or scanner gives `INSUFFICIENT` |
| Security review | JSON report | `inspect` prints provenance, coverage and reasons | Invalid schema returns usage/data error |
| Scanner crash | Scanner binary/fixture | Tool status captured with raw stderr hash | Mandatory check unresolved; no clean verdict |
| Unknown format | Unclassified file | Classifier labels unknown and assigns check applicability | Security-relevant unknown is `INSUFFICIENT` |
| Conflicting license | README vs config | Two sourced declarations + conflict record | Decision depends on policy; no false legal claim |
| Reviewer decision | Policy + evidence | Deterministic rule IDs and precedence | Unknown mandatory predicate is insufficient |
| Benchmark researcher | Fixed fixture set + baselines | Compare coverage/detection with ground truth | Unsupported baseline omitted from paired analysis |

**Normal flow:** validate canonical input and output separation → create bounded read-only snapshot → inventory + content hashes → classify → structural/metadata/dependency checks → optional ModelScan subprocess → normalize raw evidence → reconcile expected/applied/completed checks → conflict resolution → evaluate policy → serialize reports → verify original identity unchanged. **Degraded flow:** scanner unavailable or unsupported file records explicit coverage gaps and `INSUFFICIENT`. **Failure flow:** untrusted input/exhausted resources yields a controlled error; if an evidence report can be safely produced, its status is insufficient, never fabricated approval.

## 5. Functional requirements summary

P0 = essential first release, P1 = validated follow-up, P2 = gated research. The `T-*` names are planned test contracts, not existing tests.

| ID | Requirement | Priority | Expected behavior / acceptance focus | Module | Task | Test |
|---|---|---|---|---|---|---|
| FR-001 | Validate local input | P0 | Local directory, no implicit network; refuse nonexistent/unreadable/out-of-root output paths | `InputGate` | `MV-003` | `T-INPUT-01` |
| FR-002 | Bounded safe discovery | P0 | Reject symlinks, nonregular nodes, traversal and size/count budgets; no execution | `Inventory` | `MV-004` | `T-INV-01` |
| FR-003 | Artifact identity | P0 | Sorted normalized relative paths, per-file SHA-256, deterministic manifest digest; changes fail | `Identity` | `MV-005` | `T-ID-01` |
| FR-004 | File classification | P0 | Signature/extension classes and scoped applicability; unknown security-relevant file cannot silently pass | `Classifier` | `MV-006` | `T-CLASS-01` |
| FR-005 | Structural inspection | P0 | Bounded safetensors header + ZIP index checks as bytes; never deserialize | `Structural` | `MV-007` | `T-STRUCT-01` |
| FR-006 | Provenance and license claims | P0 | Collect local declarations with source pointers; classify missing/conflict, never adjudicate legal rights | `Metadata` | `MV-008` | `T-META-01` |
| FR-007 | Dependency declarations | P0 | Parse explicit local pinned-environment manifest as claims; no invented vulnerability reachability | `Dependencies` | `MV-009` | `T-DEPS-01` |
| FR-008 | ModelScan adapter | P0 | Run pinned external scanner, preserve raw output/status/version; unavailable/error is not clean | `ScannerAdapter` | `MV-010` | `T-SCAN-01` |
| FR-009 | Normalized evidence | P0 | Schema-validated, attributable check/execution/finding records, raw hash and normalization version | `Evidence` | `MV-011` | `T-EVID-01` |
| FR-010 | Coverage reconciliation | P0 | Per-file/applicable-check complete/skipped/failed/unsupported matrix; no naive clean percentage | `Coverage` | `MV-012` | `T-COV-01` |
| FR-011 | Evidence conflicts | P0 | Preserve inconsistent license/identity/scanner statements; mark decision-relevant conflicts | `Conflicts` | `MV-013` | `T-CONFLICT-01` |
| FR-012 | Deterministic admission | P0 | Versioned policy, precedence BLOCK > INSUFFICIENT > CONTROLS > APPROVE with substantiated block rule | `Policy` | `MV-014` | `T-POLICY-01` |
| FR-013 | JSON and Markdown reports | P0 | Versioned schema, evidence links, deterministic content hash, limitations, redaction | `Reports` | `MV-016` | `T-REPORT-01` |
| FR-014 | CLI contract | P0 | Scan, inspect, policy validate, doctor, version; script-safe stdout/stderr and exit codes | `CLI` | `MV-002` | `T-CLI-01` |
| FR-015 | Reproducibility and drift | P0 | Same frozen inputs/policy imply same semantic evidence; runtime metadata separate; post-scan recheck | `Identity` | `MV-017` | `T-REPRO-01` |
| FR-016 | Fixture and E2E coverage | P0 | Safe synthetic fixtures for all outcomes, fail-closed cases, one end-to-end vertical slice | `Testing` | `MV-019` | `T-E2E-01` |
| FR-017 | Independent baseline benchmark | P1 | Ground-truthed comparison with ModelScan and applicable alternatives; report unsupported fairly | `Benchmark` | `MV-022` | `T-BENCH-01` |
| FR-018 | Isolated loader verification | P2 | Opt-in microVM-only test, version/flags bound, never execute untrusted code on host | `Verification` | `MV-030` | `T-VM-01` |
| FR-019 | Advisory enrichment | P1 | Use explicitly supplied offline OSV snapshot with timestamp; network mode separate and opt-in | `Dependencies` | `MV-020` | `T-OSV-01` |
| FR-020 | Doctor diagnostics | P0 | Report dependency availability and support status without scanning or importing models | `CLI` | `MV-018` | `T-DOCTOR-01` |
| FR-021 | Loader-version discrepancy experiment | P2 | Show observed v1/v2 behavioral differences on independently checked controlled fixtures | `Verification` | `MV-031` | `T-VERSION-01` |
| FR-022 | Stored raw evidence verification | P1 | Hash every declared bounded attachment; incomplete/tampered evidence cannot verify | `Reports` | `MV-033` | `T-AUDIT-01` |
| FR-023 | Stored report comparison | P1 | Compare identities/semantic evidence without recomputing admission; bounded private output | `Reports` | `MV-034` | `T-COMPARE-01` |
| FR-024 | Batch stored-report audit | P1 | Explicit local manifest, aggregate budgets, independent row failures and no false aggregate success | `Reports` | `MV-035` | `T-BATCH-01` |

### Requirement contracts

#### FR-001 — Validate local input (P0)
**Responsible:** ModelVet core/CLI maintainer; consumer: local developer or security reviewer. **Preconditions:** artifact directory available, dependency and configuration validated; for P2, isolated runner explicitly provisioned. **Inputs:** bounded local bytes, typed policy and optional tool/metadata records applicable to this check. **Behavior:** Local directory, no implicit network; refuse nonexistent/unreadable/out-of-root output paths. **Outputs:** versioned evidence with source, check status and any limitation. **Failure:** record the reason with an `ERROR`, `FAILED`, `SKIPPED`, `UNSUPPORTED`, or `INCONCLUSIVE` status; a mandatory failure cannot become an approval. **Acceptance:** `T-INPUT-01` contains positive, negative and partial-result cases; output validates schema; re-running with identical frozen inputs has the same semantic result. **Implementation component:** `InputGate`; **task:** `MV-003`. **Dependencies:** inventory/identity and evidence contracts for applicable consumers; see TASKS for precise ordering.

#### FR-002 — Bounded safe discovery (P0)
**Responsible:** ModelVet core/CLI maintainer; consumer: local developer or security reviewer. **Preconditions:** artifact directory available, dependency and configuration validated; for P2, isolated runner explicitly provisioned. **Inputs:** bounded local bytes, typed policy and optional tool/metadata records applicable to this check. **Behavior:** Reject symlinks, nonregular nodes, traversal and size/count budgets; no execution. **Outputs:** versioned evidence with source, check status and any limitation. **Failure:** record the reason with an `ERROR`, `FAILED`, `SKIPPED`, `UNSUPPORTED`, or `INCONCLUSIVE` status; a mandatory failure cannot become an approval. **Acceptance:** `T-INV-01` contains positive, negative and partial-result cases; output validates schema; re-running with identical frozen inputs has the same semantic result. **Implementation component:** `Inventory`; **task:** `MV-004`. **Dependencies:** inventory/identity and evidence contracts for applicable consumers; see TASKS for precise ordering.

#### FR-003 — Artifact identity (P0)
**Responsible:** ModelVet core/CLI maintainer; consumer: local developer or security reviewer. **Preconditions:** artifact directory available, dependency and configuration validated; for P2, isolated runner explicitly provisioned. **Inputs:** bounded local bytes, typed policy and optional tool/metadata records applicable to this check. **Behavior:** Sorted normalized relative paths, per-file SHA-256, deterministic manifest digest; changes fail. **Outputs:** versioned evidence with source, check status and any limitation. **Failure:** record the reason with an `ERROR`, `FAILED`, `SKIPPED`, `UNSUPPORTED`, or `INCONCLUSIVE` status; a mandatory failure cannot become an approval. **Acceptance:** `T-ID-01` contains positive, negative and partial-result cases; output validates schema; re-running with identical frozen inputs has the same semantic result. **Implementation component:** `Identity`; **task:** `MV-005`. **Dependencies:** inventory/identity and evidence contracts for applicable consumers; see TASKS for precise ordering.

#### FR-004 — File classification (P0)
**Responsible:** ModelVet core/CLI maintainer; consumer: local developer or security reviewer. **Preconditions:** artifact directory available, dependency and configuration validated; for P2, isolated runner explicitly provisioned. **Inputs:** bounded local bytes, typed policy and optional tool/metadata records applicable to this check. **Behavior:** Signature/extension classes and scoped applicability; unknown security-relevant file cannot silently pass. **Outputs:** versioned evidence with source, check status and any limitation. **Failure:** record the reason with an `ERROR`, `FAILED`, `SKIPPED`, `UNSUPPORTED`, or `INCONCLUSIVE` status; a mandatory failure cannot become an approval. **Acceptance:** `T-CLASS-01` contains positive, negative and partial-result cases; output validates schema; re-running with identical frozen inputs has the same semantic result. **Implementation component:** `Classifier`; **task:** `MV-006`. **Dependencies:** inventory/identity and evidence contracts for applicable consumers; see TASKS for precise ordering.

#### FR-005 — Structural inspection (P0)
**Responsible:** ModelVet core/CLI maintainer; consumer: local developer or security reviewer. **Preconditions:** artifact directory available, dependency and configuration validated; for P2, isolated runner explicitly provisioned. **Inputs:** bounded local bytes, typed policy and optional tool/metadata records applicable to this check. **Behavior:** Bounded safetensors header + ZIP index checks as bytes; never deserialize. **Outputs:** versioned evidence with source, check status and any limitation. **Failure:** record the reason with an `ERROR`, `FAILED`, `SKIPPED`, `UNSUPPORTED`, or `INCONCLUSIVE` status; a mandatory failure cannot become an approval. **Acceptance:** `T-STRUCT-01` contains positive, negative and partial-result cases; output validates schema; re-running with identical frozen inputs has the same semantic result. **Implementation component:** `Structural`; **task:** `MV-007`. **Dependencies:** inventory/identity and evidence contracts for applicable consumers; see TASKS for precise ordering.

#### FR-006 — Provenance and license claims (P0)
**Responsible:** ModelVet core/CLI maintainer; consumer: local developer or security reviewer. **Preconditions:** artifact directory available, dependency and configuration validated; for P2, isolated runner explicitly provisioned. **Inputs:** bounded local bytes, typed policy and optional tool/metadata records applicable to this check. **Behavior:** Collect local declarations with source pointers; classify missing/conflict, never adjudicate legal rights. **Outputs:** versioned evidence with source, check status and any limitation. **Failure:** record the reason with an `ERROR`, `FAILED`, `SKIPPED`, `UNSUPPORTED`, or `INCONCLUSIVE` status; a mandatory failure cannot become an approval. **Acceptance:** `T-META-01` contains positive, negative and partial-result cases; output validates schema; re-running with identical frozen inputs has the same semantic result. **Implementation component:** `Metadata`; **task:** `MV-008`. **Dependencies:** inventory/identity and evidence contracts for applicable consumers; see TASKS for precise ordering.

#### FR-007 — Dependency declarations (P0)
**Responsible:** ModelVet core/CLI maintainer; consumer: local developer or security reviewer. **Preconditions:** artifact directory available, dependency and configuration validated; for P2, isolated runner explicitly provisioned. **Inputs:** bounded local bytes, typed policy and optional tool/metadata records applicable to this check. **Behavior:** Parse explicit local pinned-environment manifest as claims; no invented vulnerability reachability. **Outputs:** versioned evidence with source, check status and any limitation. **Failure:** record the reason with an `ERROR`, `FAILED`, `SKIPPED`, `UNSUPPORTED`, or `INCONCLUSIVE` status; a mandatory failure cannot become an approval. **Acceptance:** `T-DEPS-01` contains positive, negative and partial-result cases; output validates schema; re-running with identical frozen inputs has the same semantic result. **Implementation component:** `Dependencies`; **task:** `MV-009`. **Dependencies:** inventory/identity and evidence contracts for applicable consumers; see TASKS for precise ordering.

#### FR-008 — ModelScan adapter (P0)
**Responsible:** ModelVet core/CLI maintainer; consumer: local developer or security reviewer. **Preconditions:** artifact directory available, dependency and configuration validated; for P2, isolated runner explicitly provisioned. **Inputs:** bounded local bytes, typed policy and optional tool/metadata records applicable to this check. **Behavior:** Run pinned external scanner, preserve raw output/status/version; unavailable/error is not clean. **Outputs:** versioned evidence with source, check status and any limitation. **Failure:** record the reason with an `ERROR`, `FAILED`, `SKIPPED`, `UNSUPPORTED`, or `INCONCLUSIVE` status; a mandatory failure cannot become an approval. **Acceptance:** `T-SCAN-01` contains positive, negative and partial-result cases; output validates schema; re-running with identical frozen inputs has the same semantic result. **Implementation component:** `ScannerAdapter`; **task:** `MV-010`. **Dependencies:** inventory/identity and evidence contracts for applicable consumers; see TASKS for precise ordering.

#### FR-009 — Normalized evidence (P0)
**Responsible:** ModelVet core/CLI maintainer; consumer: local developer or security reviewer. **Preconditions:** artifact directory available, dependency and configuration validated; for P2, isolated runner explicitly provisioned. **Inputs:** bounded local bytes, typed policy and optional tool/metadata records applicable to this check. **Behavior:** Schema-validated, attributable check/execution/finding records, raw hash and normalization version. **Outputs:** versioned evidence with source, check status and any limitation. **Failure:** record the reason with an `ERROR`, `FAILED`, `SKIPPED`, `UNSUPPORTED`, or `INCONCLUSIVE` status; a mandatory failure cannot become an approval. **Acceptance:** `T-EVID-01` contains positive, negative and partial-result cases; output validates schema; re-running with identical frozen inputs has the same semantic result. **Implementation component:** `Evidence`; **task:** `MV-011`. **Dependencies:** inventory/identity and evidence contracts for applicable consumers; see TASKS for precise ordering.

#### FR-010 — Coverage reconciliation (P0)
**Responsible:** ModelVet core/CLI maintainer; consumer: local developer or security reviewer. **Preconditions:** artifact directory available, dependency and configuration validated; for P2, isolated runner explicitly provisioned. **Inputs:** bounded local bytes, typed policy and optional tool/metadata records applicable to this check. **Behavior:** Per-file/applicable-check complete/skipped/failed/unsupported matrix; no naive clean percentage. **Outputs:** versioned evidence with source, check status and any limitation. **Failure:** record the reason with an `ERROR`, `FAILED`, `SKIPPED`, `UNSUPPORTED`, or `INCONCLUSIVE` status; a mandatory failure cannot become an approval. **Acceptance:** `T-COV-01` contains positive, negative and partial-result cases; output validates schema; re-running with identical frozen inputs has the same semantic result. **Implementation component:** `Coverage`; **task:** `MV-012`. **Dependencies:** inventory/identity and evidence contracts for applicable consumers; see TASKS for precise ordering.

#### FR-011 — Evidence conflicts (P0)
**Responsible:** ModelVet core/CLI maintainer; consumer: local developer or security reviewer. **Preconditions:** artifact directory available, dependency and configuration validated; for P2, isolated runner explicitly provisioned. **Inputs:** bounded local bytes, typed policy and optional tool/metadata records applicable to this check. **Behavior:** Preserve inconsistent license/identity/scanner statements; mark decision-relevant conflicts. **Outputs:** versioned evidence with source, check status and any limitation. **Failure:** record the reason with an `ERROR`, `FAILED`, `SKIPPED`, `UNSUPPORTED`, or `INCONCLUSIVE` status; a mandatory failure cannot become an approval. **Acceptance:** `T-CONFLICT-01` contains positive, negative and partial-result cases; output validates schema; re-running with identical frozen inputs has the same semantic result. **Implementation component:** `Conflicts`; **task:** `MV-013`. **Dependencies:** inventory/identity and evidence contracts for applicable consumers; see TASKS for precise ordering.

#### FR-012 — Deterministic admission (P0)
**Responsible:** ModelVet core/CLI maintainer; consumer: local developer or security reviewer. **Preconditions:** artifact directory available, dependency and configuration validated; for P2, isolated runner explicitly provisioned. **Inputs:** bounded local bytes, typed policy and optional tool/metadata records applicable to this check. **Behavior:** Versioned policy, precedence BLOCK > INSUFFICIENT > CONTROLS > APPROVE with substantiated block rule. **Outputs:** versioned evidence with source, check status and any limitation. **Failure:** record the reason with an `ERROR`, `FAILED`, `SKIPPED`, `UNSUPPORTED`, or `INCONCLUSIVE` status; a mandatory failure cannot become an approval. **Acceptance:** `T-POLICY-01` contains positive, negative and partial-result cases; output validates schema; re-running with identical frozen inputs has the same semantic result. **Implementation component:** `Policy`; **task:** `MV-014`. **Dependencies:** inventory/identity and evidence contracts for applicable consumers; see TASKS for precise ordering.

#### FR-013 — JSON and Markdown reports (P0)
**Responsible:** ModelVet core/CLI maintainer; consumer: local developer or security reviewer. **Preconditions:** artifact directory available, dependency and configuration validated; for P2, isolated runner explicitly provisioned. **Inputs:** bounded local bytes, typed policy and optional tool/metadata records applicable to this check. **Behavior:** Versioned schema, evidence links, deterministic content hash, limitations, redaction. **Outputs:** versioned evidence with source, check status and any limitation. **Failure:** record the reason with an `ERROR`, `FAILED`, `SKIPPED`, `UNSUPPORTED`, or `INCONCLUSIVE` status; a mandatory failure cannot become an approval. **Acceptance:** `T-REPORT-01` contains positive, negative and partial-result cases; output validates schema; re-running with identical frozen inputs has the same semantic result. **Implementation component:** `Reports`; **task:** `MV-016`. **Dependencies:** inventory/identity and evidence contracts for applicable consumers; see TASKS for precise ordering.

#### FR-014 — CLI contract (P0)
**Responsible:** ModelVet core/CLI maintainer; consumer: local developer or security reviewer. **Preconditions:** artifact directory available, dependency and configuration validated; for P2, isolated runner explicitly provisioned. **Inputs:** bounded local bytes, typed policy and optional tool/metadata records applicable to this check. **Behavior:** Scan, inspect, policy validate, doctor, version; script-safe stdout/stderr and exit codes. **Outputs:** versioned evidence with source, check status and any limitation. **Failure:** record the reason with an `ERROR`, `FAILED`, `SKIPPED`, `UNSUPPORTED`, or `INCONCLUSIVE` status; a mandatory failure cannot become an approval. **Acceptance:** `T-CLI-01` contains positive, negative and partial-result cases; output validates schema; re-running with identical frozen inputs has the same semantic result. **Implementation component:** `CLI`; **task:** `MV-002`. **Dependencies:** inventory/identity and evidence contracts for applicable consumers; see TASKS for precise ordering.

#### FR-015 — Reproducibility and drift (P0)
**Responsible:** ModelVet core/CLI maintainer; consumer: local developer or security reviewer. **Preconditions:** artifact directory available, dependency and configuration validated; for P2, isolated runner explicitly provisioned. **Inputs:** bounded local bytes, typed policy and optional tool/metadata records applicable to this check. **Behavior:** Same frozen inputs/policy imply same semantic evidence; runtime metadata separate; post-scan recheck. **Outputs:** versioned evidence with source, check status and any limitation. **Failure:** record the reason with an `ERROR`, `FAILED`, `SKIPPED`, `UNSUPPORTED`, or `INCONCLUSIVE` status; a mandatory failure cannot become an approval. **Acceptance:** `T-REPRO-01` contains positive, negative and partial-result cases; output validates schema; re-running with identical frozen inputs has the same semantic result. **Implementation component:** `Identity`; **task:** `MV-017`. **Dependencies:** inventory/identity and evidence contracts for applicable consumers; see TASKS for precise ordering.

#### FR-016 — Fixture and E2E coverage (P0)
**Responsible:** ModelVet core/CLI maintainer; consumer: local developer or security reviewer. **Preconditions:** artifact directory available, dependency and configuration validated; for P2, isolated runner explicitly provisioned. **Inputs:** bounded local bytes, typed policy and optional tool/metadata records applicable to this check. **Behavior:** Safe synthetic fixtures for all outcomes, fail-closed cases, one end-to-end vertical slice. **Outputs:** versioned evidence with source, check status and any limitation. **Failure:** record the reason with an `ERROR`, `FAILED`, `SKIPPED`, `UNSUPPORTED`, or `INCONCLUSIVE` status; a mandatory failure cannot become an approval. **Acceptance:** `T-E2E-01` contains positive, negative and partial-result cases; output validates schema; re-running with identical frozen inputs has the same semantic result. **Implementation component:** `Testing`; **task:** `MV-019`. **Dependencies:** inventory/identity and evidence contracts for applicable consumers; see TASKS for precise ordering.

#### FR-017 — Independent baseline benchmark (P1)
**Responsible:** ModelVet core/CLI maintainer; consumer: local developer or security reviewer. **Preconditions:** artifact directory available, dependency and configuration validated; for P2, isolated runner explicitly provisioned. **Inputs:** bounded local bytes, typed policy and optional tool/metadata records applicable to this check. **Behavior:** Ground-truthed comparison with ModelScan and applicable alternatives; report unsupported fairly. **Outputs:** versioned evidence with source, check status and any limitation. **Failure:** record the reason with an `ERROR`, `FAILED`, `SKIPPED`, `UNSUPPORTED`, or `INCONCLUSIVE` status; a mandatory failure cannot become an approval. **Acceptance:** `T-BENCH-01` contains positive, negative and partial-result cases; output validates schema; re-running with identical frozen inputs has the same semantic result. **Implementation component:** `Benchmark`; **task:** `MV-022`. **Dependencies:** inventory/identity and evidence contracts for applicable consumers; see TASKS for precise ordering.

#### FR-018 — Isolated loader verification (P2)
**Responsible:** ModelVet core/CLI maintainer; consumer: local developer or security reviewer. **Preconditions:** artifact directory available, dependency and configuration validated; for P2, isolated runner explicitly provisioned. **Inputs:** bounded local bytes, typed policy and optional tool/metadata records applicable to this check. **Behavior:** Opt-in microVM-only test, version/flags bound, never execute untrusted code on host. **Outputs:** versioned evidence with source, check status and any limitation. **Failure:** record the reason with an `ERROR`, `FAILED`, `SKIPPED`, `UNSUPPORTED`, or `INCONCLUSIVE` status; a mandatory failure cannot become an approval. **Acceptance:** `T-VM-01` contains positive, negative and partial-result cases; output validates schema; re-running with identical frozen inputs has the same semantic result. **Implementation component:** `Verification`; **task:** `MV-030`. **Dependencies:** inventory/identity and evidence contracts for applicable consumers; see TASKS for precise ordering.

#### FR-019 — Advisory enrichment (P1)
**Responsible:** ModelVet core/CLI maintainer; consumer: local developer or security reviewer. **Preconditions:** artifact directory available, dependency and configuration validated; for P2, isolated runner explicitly provisioned. **Inputs:** bounded local bytes, typed policy and optional tool/metadata records applicable to this check. **Behavior:** Use explicitly supplied offline OSV snapshot with timestamp; network mode separate and opt-in. **Outputs:** versioned evidence with source, check status and any limitation. **Failure:** record the reason with an `ERROR`, `FAILED`, `SKIPPED`, `UNSUPPORTED`, or `INCONCLUSIVE` status; a mandatory failure cannot become an approval. **Acceptance:** `T-OSV-01` contains positive, negative and partial-result cases; output validates schema; re-running with identical frozen inputs has the same semantic result. **Implementation component:** `Dependencies`; **task:** `MV-020`. **Dependencies:** inventory/identity and evidence contracts for applicable consumers; see TASKS for precise ordering.

#### FR-020 — Doctor diagnostics (P0)
**Responsible:** ModelVet core/CLI maintainer; consumer: local developer or security reviewer. **Preconditions:** artifact directory available, dependency and configuration validated; for P2, isolated runner explicitly provisioned. **Inputs:** bounded local bytes, typed policy and optional tool/metadata records applicable to this check. **Behavior:** Report dependency availability and support status without scanning or importing models. **Outputs:** versioned evidence with source, check status and any limitation. **Failure:** record the reason with an `ERROR`, `FAILED`, `SKIPPED`, `UNSUPPORTED`, or `INCONCLUSIVE` status; a mandatory failure cannot become an approval. **Acceptance:** `T-DOCTOR-01` contains positive, negative and partial-result cases; output validates schema; re-running with identical frozen inputs has the same semantic result. **Implementation component:** `CLI`; **task:** `MV-018`. **Dependencies:** inventory/identity and evidence contracts for applicable consumers; see TASKS for precise ordering.

#### FR-021 — Loader-version discrepancy experiment (P2)
**Responsible:** ModelVet core/CLI maintainer; consumer: local developer or security reviewer. **Preconditions:** artifact directory available, dependency and configuration validated; for P2, isolated runner explicitly provisioned. **Inputs:** bounded local bytes, typed policy and optional tool/metadata records applicable to this check. **Behavior:** Show observed v1/v2 behavioral differences on independently checked controlled fixtures. **Outputs:** versioned evidence with source, check status and any limitation. **Failure:** record the reason with an `ERROR`, `FAILED`, `SKIPPED`, `UNSUPPORTED`, or `INCONCLUSIVE` status; a mandatory failure cannot become an approval. **Acceptance:** `T-VERSION-01` contains positive, negative and partial-result cases; output validates schema; re-running with identical frozen inputs has the same semantic result. **Implementation component:** `Verification`; **task:** `MV-031`. **Dependencies:** inventory/identity and evidence contracts for applicable consumers; see TASKS for precise ordering.


## 6. Non-functional requirements

| NFR | Quality bar | Verification |
|---|---|---|
| NFR-01 security | Zero model deserialization or arbitrary repo-code import in ordinary process; no shell interpolation | Static review + hostile-fixture integration test |
| NFR-02 fail closed | Mandatory status other than `COMPLETE` prevents `APPROVE` and `CONTROLS`, absent explicit independent blocking evidence | Property tests of all status combinations |
| NFR-03 integrity | File and repository digest bound to output; input mutation detected before decision is finalized | Induced mid-scan modification test |
| NFR-04 budgets | Proposed defaults: ≤10,000 files, ≤1 GiB individual file, ≤2 GiB aggregate, ≤16 MiB metadata read, 120s scanner timeout; all configurable below hard ceilings | Synthetic sizes + timeout tests; performance to be measured |
| NFR-05 determinism | Canonical semantic report excluding observation timestamps/run IDs byte-identical from frozen evidence/policy | Repeat-evaluation digest test |
| NFR-06 portability | POSIX Linux/macOS for pure static MVP; Windows unsupported until tested; P2 Linux KVM only | OS CI matrix and doctor capability matrix |
| NFR-07 maintainability | No mandatory paid API/cloud/database; strict type boundaries; modular monolith | Dependency review and import-cycle check |
| NFR-08 audit | Every finding names evidence producer/version/check/source; no naked risk score | Schema tests and report review |
| NFR-09 CLI access | `NO_COLOR`, noninteractive mode, plain text status independent of ANSI color, useful stderr | CLI snapshot tests |
| NFR-10 observability | Bounded structured logs with secrets/path redaction; debug does not dump model contents | Log privacy fixtures |
| NFR-11 testability | Unit + property + adapter contract + E2E + fixture integrity checks; targets proposed not achieved | Coverage measured at gate; security cases assessed separately |
| NFR-12 dependency safety | Lockfile committed after resolution, scanner pinned and smoke-tested; report exact versions | `uv lock --check`, vulnerability scan, compatibility test |

**Targets are engineering budgets, not measured throughput or security guarantees.** Reject over-budget input deterministically rather than silently truncating evidence. For larger real models, re-evaluate budgets before expanding scope.

## 7. Decision and precedence contract

- `APPROVE`: all mandatory assessment predicates `COMPLETE`, no prohibited findings, no unresolved relevant conflicts, and no controls required. *Scoped policy approval, not proof of harmlessness.*
- `CONTROLS`: all mandatory predicates `COMPLETE`, no block or unresolved relevant conflict, but policy requires named, enforceable conditions (control IDs and owner). It **does not mean unconditional access**.
- `BLOCK`: evidence substantiates an explicit prohibited condition (e.g., prohibited active repository code confirmed by inventory and policy rule; high-confidence independently verified violation). `BLOCK` may supersede other missing evidence only when the block reason itself is independent and complete; scanner allegation with unknown provenance is not automatically enough.
- `INSUFFICIENT`: mandatory evidence missing, skipped, errored, timed out, unsupported, identity drift, ambiguous status, or decision-relevant unresolved conflicts without an independently justified block.

**Precedence:** independently substantiated `BLOCK` → `INSUFFICIENT` → `CONTROLS` → `APPROVE`. Rules must be versioned and evaluated on canonical evidence; severity labels and scanner exit codes cannot directly map to a decision. Nonmandatory check missing is disclosed but need not force insufficiency if policy explicitly allows it. Overrides cannot silently force approval; a future signed human exception is out of MVP.

## 8. Evidence and coverage semantics

Check statuses: `COMPLETE`, `SKIPPED`, `FAILED`, `UNSUPPORTED`, `INCONCLUSIVE`, `NOT_RUN` (execution state) and separate `result: FINDINGS | NO_FINDINGS | UNKNOWN`. Scanner findings are `REPORTED`, `CORROBORATED` or `DISPUTED`; ModelVet does not infer `CORROBORATED` solely by repeating scanner text. Each evidence object includes URI/path ID, tool and version, input artifact hash, check ID, timestamp, bounded raw-report hash, normalization version and limitations. Coverage records are per-file **and** per-applicable-check; a count of scanned files is never proof of overall safety. Raw scanner report is retained with size cap and safe handling; normalization must not erase skipped/error details.

## 9. Report output contract

`schema_version: 1.0.0`, `artifact`, `manifest_digest`, `run`, `policy`, `tools`, `files`, `checks`, `findings`, `coverage`, `conflicts`, `decision`, `limitations`, and `semantic_digest`. Markdown includes executive verdict, exact file identity, policies/checks used, coverage table, findings, declarations/conflicts, exceptions, limitations and reproduction metadata. Report artifacts written atomically outside scanned input, restrictive permissions where available. Report may include sensitive paths: redact by default.

Illustrative, **not a real scan result**:

```json
{
  "schema_version": "1.0.0",
  "artifact": {"manifest_digest": "sha256:ILLUSTRATIVE"},
  "run": {"id": "EXAMPLE-ONLY", "status": "COMPLETE"},
  "policy": {"id": "default", "version": "1"},
  "checks": [{"id": "modelscan:weights.pt", "status": "UNSUPPORTED", "result": "UNKNOWN"}],
  "coverage": {"mandatory_unresolved": ["modelscan:weights.pt"]},
  "decision": {"state": "INSUFFICIENT", "rule_ids": ["MISSING-MANDATORY"], "reason": "Required scanner coverage unavailable"},
  "limitations": ["No dynamic loader execution performed"]
}
```

## 10. CLI exit contract

`0 APPROVE`, `10 CONTROLS`, `20 BLOCK`, `30 INSUFFICIENT`, `40 invalid input/config/schema`, `50 internal/tool orchestration failure before valid decision`, `130 interrupted`. An individual scanner exit of 1/2/3/4 is normalized to a tool status; never forwarded directly as a ModelVet decision. `doctor`, `version`, `policy validate`, `inspect` use `0` for success and `40`/`50` for failures. A scanner crash *during a completed assessment orchestration* produces a report plus `INSUFFICIENT (30)`; if no trustworthy report can be produced, `50`. Reports should be written even for `BLOCK` and `INSUFFICIENT` when safe.

## 11. Error table

| Condition | Output/check status | Decision/error |
|---|---|---|
| Missing input / not directory | No scan | exit 40 |
| Symlink, FIFO, socket, device / path escape | Input rejection | exit 40 or insufficient report if safely attributable |
| Too many files / bytes | Input rejection | exit 40; no partial approval |
| Hash changes during snapshot/scan | `FAILED` identity | `INSUFFICIENT`, exit 30 |
| Unsupported security-relevant format | `UNSUPPORTED` check | `INSUFFICIENT`, exit 30 |
| ModelScan missing/version mismatched | `NOT_RUN` | `INSUFFICIENT`, exit 30 if required |
| Scanner timeout/crash/malformed JSON | `FAILED` + raw error metadata | `INSUFFICIENT`, exit 30 |
| Report destination inside input | Input rejection | exit 40 |
| License declarations conflict | `conflict` record | policy-dependent `INSUFFICIENT`/`BLOCK` |
| Proven malicious operation verified | `CORROBORATED` finding | `BLOCK` if specific prohibition applies |
| Advisory snapshot stale | `INCONCLUSIVE` advisory check | `INSUFFICIENT` when mandatory |
| Keyboard interrupt | no provisional APPROVE | exit 130 |

## 12. MVP end-to-end acceptance scenario

Given a small local synthetic fixture containing `config.json`, `README.md` and a deliberately malformed-but-non-executable `.safetensors` header, with a validated default policy and pinned scanner adapter, when `modelvet scan tests/fixtures/e2e/sample --out <safe-temp>` runs, then it must produce schema-valid JSON and Markdown; file SHA-256 and manifest digest; structural check `FAILED`; coverage explicitly incomplete; decision `INSUFFICIENT`; exit `30`; no model loader imported; repeated evaluation of frozen evidence/policy produces identical semantic digest. A separate fixture with an explicitly forbidden `.py` loader plus verified inventory should produce a correctly reasoned `BLOCK`; a safe fixture may `APPROVE` only when **all configured** mandatory checks pass.

## 13. Release gate and exclusions

All P0 requirements have linked tasks and tests in the table, completed verification commands, and no known fail-open regression; package builds, CI passes on supported systems, reports redact host paths, benchmark claims remain clearly hypothetical. First public release does **not** include loading unknown models. P1 baseline comparisons, offline advisory enrichment and P2 controlled loader experiments are explicitly separate.

## 14. Traceability

Every row in section 5 is authoritative mapping `FR-### → module → MV-### → T-...`; `docs/TASKS.md` maps each task to a phase and exact verification. `docs/SPEC_AUDIT.md` contains automated documentation checks; `docs/PROGRESS.md` contains actual completion state, verification logs and pending release gates.

## FR-019 implementation checkpoint — 2026-10-20

MV-020 implements a separate optional offline advisory supplement on stored dependency declarations. Exact enumerated PyPI versions are matched using explicit query-scoped snapshots; unsupported ranges/ecosystems remain unresolved. The command does not mutate/recompute static admission; an operational requirement must enforce both scan and advisory command exits. ADVISORY_SPEC and PROGRESS record the interface, limitations and passing T-OSV-01 cases. Benchmark and loader requirements remain unimplemented.

## FR-017 development checkpoint — 2026-10-20

MV-022/023 engineering now supplies ten inert development recipes, frozen identities/method labels, a validated pilot runner, raw evidence, fair input-context eligibility and null efficacy metrics where reviewed data is absent. A real ModelScan 0.8.8 two-repeat local pilot is explicitly INCONCLUSIVE. This does not complete the independent baseline benchmark requirement: hidden holdout, independent adjudication and broader eligible comparisons remain pending by user selection. No loader execution requirement is implemented; PH-11 gates remain in force.

## Local static report extension — FR-022–024

The user explicitly selected “Extend the local feature plan.” PH-12–14 extend the local static CLI while externally gated research remains pending. PH-12–14 add raw-attachment verification, report comparison and explicit-manifest batch auditing. They consume existing stored reports, never load models, recalculate admission or imply author authentication. New task/FR IDs extend the original register without renumbering it. This is implementation scope, not acceptance of the proposed ADRs or external security gates. See REPORT_AUDIT_SPEC for finite budgets, privacy and command semantics.
