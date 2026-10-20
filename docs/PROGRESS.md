# ModelVet progress dashboard

**Updated 2026-10-20. Overall: local static candidate complete through PH-10. Hosted CI/public release PENDING by user-selected scope.** The five MVP commands, optional offline advisory command and three stored-report audit commands work. PH-12–14 are complete. Work started against base `e2f2bb269683d79cd6a12757aa140357fef089ad`; a newer checkpoint `af86ffee5c7b4f1e990e9dbbdba6625e973acef0` appeared during this run outside the agent commands and was preserved. Further external checkpoints were observed and preserved; the prior pilot checkpoint is recorded in `verification/MV-023/`; current extension source/build identities are in `verification/MV-035/`. Only a synthetic development pilot ran; no model loading or independently adjudicated benchmark.

| Workstream | Actual state | Evidence |
|---|---|---|
| Product definition | Drafted, pending review | `../PRD.md` |
| Architecture and threat model | Drafted, pending review | `ARCHITECTURE.md`, `THREAT_MODEL.md` |
| Dependency resolution / lock | COMPLETE for foundation | `../pyproject.toml`, `../uv.lock`, `verification/MV-001/` |
| Source implementation | Full local CLI, static checks, evidence/coverage/policy, reports and packaging | `../src/modelvet/` |
| Tests/fixtures | 558 passed / one Linux-only skip | `verification/MV-035/gate.log` |
| Benchmarks | INCONCLUSIVE local development pilot; independent research PENDING | `../benchmarks/results/`, `verification/MV-023/` |
| Isolated model-loading safety | DEFERRED | PH-11 / ADR-009 proposed |
| Release | NOT RELEASED | Local wheel/sdist verified; hosted CI/public release pending |

**Active task:** none; the requested PH-12–14 / MV-033–035 local extension is complete. **Next gates:** independent corpus/security review and dedicated Linux/KVM prerequisites, left pending by user selection. **Next external gate:** hosted CI and explicit project review. ADRs remain Proposed; provisional toolchain choices and deviations are recorded in ADR-002.

## Milestones

| Phase | Status | Notes |
|---|---|---|
| PH-01 | COMPLETE | MV-001–002 verified on macOS |
| PH-02 | COMPLETE | MV-003–006, 81 total tests; macOS gate |
| PH-03 | COMPLETE | MV-007–009 verified; static subset documented |
| PH-04 | COMPLETE | MV-010–013; 201-test final gate on macOS |
| PH-05 | COMPLETE | MV-014–015; 287-test macOS final gate |
| PH-06 | COMPLETE | MV-016–018; 317 tests, macOS |
| PH-07 | COMPLETE | MV-019/021; 345-test macOS gate |
| PH-08 | LOCAL ENGINEERING IMPLEMENTED; research PENDING | MV-020 plus development corpus/pilot; no hidden holdout/independent adjudication |
| PH-09 | LOCAL CANDIDATE COMPLETE; hosted CI PENDING | MV-024–026, scope explicitly selected by user |
| PH-10 | LOCAL CANDIDATE COMPLETE; public release PENDING | MV-027–029 verified; 381 pass / one Linux-only skip |
| PH-11 | GATED; execution NOT STARTED | Proposed review packet prepared; no reviewed Linux/KVM environment |
| PH-12 | COMPLETE | Raw evidence verification; 508 pass / one Linux-only skip |
| PH-13 | COMPLETE | Stored report comparison; 521 pass / one Linux-only skip |
| PH-14 | COMPLETE | Explicit report batch audit; 558 pass / one Linux-only skip |

## Decisions awaiting approval

`ADR-001` through `ADR-012` are **Proposed**. Priority: ADR-002 (Python+dependency choice), ADR-003 (snapshot budgets), ADR-005 (policy precedence), ADR-006 (external scanner), ADR-009 (no execution in MVP).

## Known risks / blockers

- ModelScan 0.8.8 named standalone-file coverage is observed and normalized. Archive/member completeness stays INCONCLUSIVE; Darwin memory enforcement is UNSUPPORTED required resource evidence.
- Core and separate pinned ModelScan environments pass macOS checks. Linux portability and hardening remain unverified.
- Safe snapshot budget limits practicality for multi-GB real models; scope stays bounded.
- Commercial scanner baselines and P2 isolation cannot be truthfully tested with current local static implementation.
- License/provenance metadata cannot establish legal clearance; advisory snapshots may be stale.

## Verification results

MV-001 evidence: `verification/MV-001/README.md`, on macOS arm64/Python 3.12.15/uv 0.13.3. Required lock/sync/import/isolated-build chain exit 0; 3 tests passed; lint, format, mypy and dependency consistency passed. Fresh dependency-free wheel import passed. All 30 third-party packages have saved license/notice evidence; PyPI/OSV returned no advisory matches at query time. Initial failed checks are retained. This verifies packaging, not model security or release readiness.

## Progress log

- **2026-10-20:** documentation-only blueprint created in a new folder because no existing project repository was present; defined PRD, proposed architecture/stack, 32 planned tasks, 11 phases, and future gating. No app code or benchmarks.
- **2026-10-20:** MV-001 completed in the actual Git checkout. Added package metadata, Python pin, lock, ignore rules, package init and smoke tests; installed the development toolchain and retained verification/license/advisory evidence. Next: MV-002.

## Update rules for subsequent agents

On completing an individual task: edit only its status from NOT STARTED to COMPLETE *with verification evidence*, update phase state and this log, link test output, summarize outstanding risk. If blocked mark BLOCKED with exact reason. Do not mark an entire phase done until all P0 phase tasks pass gate. Do not claim benchmark accuracy without stored reproducible measurements and dataset provenance.

- **2026-10-20:** MV-002 / PH-01 complete. CLI command grammar, placeholder errors, exit contract, plain help and machine output verified (21 targeted/24 total tests). See `verification/MV-002/`; no artifact assessment yet.

- **2026-10-20:** MV-003 complete: 15 path/budget tests, 39 full-suite tests; lint/types pass (`verification/MV-003/`). CLI now rejects invalid input/output/limits with 40; valid scans remain unavailable (50).

- **2026-10-20:** MV-004 complete: 17 snapshot tests, 56 total; lint/types pass. Private streaming copy, unsafe-node rejection, mutation checks and cleanup verified (`verification/MV-004/`).

- **2026-10-20:** MV-005 complete: 11 identity tests, 67 total; lint/types pass (`verification/MV-005/`). Implemented manifest-v1, domain-separated file IDs, and bounded source/snapshot drift checks.

- **2026-10-20:** MV-006 / PH-02 complete: 14 classifier tests, 81 total; lint/format/types/lock/build pass (`verification/MV-006/`). Applicability is explicit; no scanner or admission decision implemented yet.

- **2026-10-20:** MV-007 complete: 32 structural tests, 113 total; lint/types pass. Safetensors bounded header and classic ZIP index checks implemented; unsupported variants remain explicit (`verification/MV-007/`).

- **2026-10-20:** MV-008 complete: 11 metadata tests, 124 total; lint/types pass. Declared license/provenance sources and missing kinds preserved; no legal/adversarial truth inferred (`verification/MV-008/`).

- **2026-10-20:** MV-009 / PH-03 complete: 15 dependency tests, 139 total; lint/format/types/lock/build pass (`verification/MV-009/`). Explicit local environment claims supported, no network/advisory or installed-package inference.

- **2026-10-20 final PH-03 gate:** 140 tests passed; lock, lint, formatting, mypy and isolated wheel/sdist build all exit 0. Exact combined log: `verification/PH-03/final-gate.log`. Scan remains an explicit unavailable command after path validation. MV-010 is next; PyPI reports ModelScan 0.8.8, whose Rich/TOML requirements differ from the core lock, so PH-04 must keep its environment separate. No ModelScan install/run or normalization has been performed.

- **2026-10-20:** MV-010 complete: 17 contract tests, 157 total; real ModelScan 0.8.8 smoke and both environment checks pass (`verification/MV-010/`). External eight-package scanner environment has separate hash lock and license/advisory evidence. Darwin memory-limit APIs reject tested caps; CPU/output/file/FD/wall limits work, but memory resource coverage must remain unresolved. No admission engine yet.

- **2026-10-20:** MV-011 complete: 21 evidence tests, 178 total; lint/format/types/build pass. Real version-pinned output normalizes to explicit scanned/skipped/resource states (`verification/MV-011/`). Applicability v2 adds mandatory scanner resource expectations; archive member proof remains inconclusive.

- **2026-10-20:** MV-012 complete: 13 coverage tests, 191 total; lint/format/types/build pass (`verification/MV-012/`). Expected and observed checks are joined independently, with explicit mandatory and NOT_RUN buckets; duplicates cannot complete a check.

- **2026-10-20 final PH-04 gate:** MV-013 and PH-04 complete. 201 tests pass; lock/lint/format/mypy/wheel+sdist build exit 0 (`verification/PH-04/final-gate.log`). A nested JsonValue NaN case failed first and now has explicit finite/Unicode/structure validation; failure log retained. Policy evaluation, report generation and complete CLI orchestration remain pending; valid scan still returns unavailable/50. Next: MV-014, then MV-015.

- **2026-10-20:** MV-014 complete: 27 targeted / 228 total tests, lint and mypy pass (`verification/MV-014/`). Evaluator recomputes expected coverage, binds core identity/classification facts, requires independent complete source-ban evidence, and preserves named control owners. The 1,296 status combinations are checked under two policy modes. No TOML parser, scan/report orchestration or release yet.

- **2026-10-20 final PH-05 gate:** MV-015 / PH-05 complete. 58 config tests and 29 evaluator tests (287 total) pass; lock/lint/format/mypy (38 source files)/wheel+sdist build exit 0 (`verification/PH-05/final-gate.log`). Fresh locked-runtime wheel installation loads the embedded default; all five packaged schemas match source. One initial parent-symlink error was fixed to a controlled invalid-input failure. Policy validation now succeeds or returns 40 without leaking policy contents. No dependency additions. Scan/inspect/doctor and full report orchestration remain unavailable; next MV-016. Scanner archive proof and Darwin memory gaps remain unresolved; Linux/release/benchmark/loader gates remain pending.

- **2026-10-20:** MV-016 complete: 19 targeted / 306 total tests, lint/types pass (`verification/MV-016/gate.log`). JSON+Markdown reports validate identity, coverage, references and semantic digest; output directories/files are 0700/0600, report.json is written last as completion marker. Exact artifact filenames and restricted raw bytes remain sensitive. Next MV-017.

- **2026-10-20:** MV-017 complete: 8 targeted / 314 total tests, lint/types pass (`verification/MV-017/gate.log`). Run/vendor timestamps, raw hashes and temp environment digests remain observational; artifact/policy/tool/check/decision semantics remain bound. Source or snapshot changes fail identity for final evaluation. Next MV-018.

- **2026-10-20 PH-06 complete:** MV-018: 5 targeted / 317 total tests, lint/types/build pass (`verification/MV-018/gate.log`). Inspect/doctor/version work; doctor exit 0 means probe completed, with readiness and limitations reported separately. Reports retain original raw evidence privately and redact free text; checks use an explicit source-reference index. Next PH-07 MV-019 scan service/E2E, then MV-021 fault injection.

- **2026-10-20:** MV-019 complete: 11 E2E / 327 total tests, lint/types pass (`verification/MV-019/gate.log`). Full CLI scan now writes schema-valid JSON/Markdown with all four decision exits. Temp cleanup succeeds before report publication; final identity check precedes final policy. Next MV-021 fault injection.

- **2026-10-20 PH-07 complete:** MV-021: 18 fault cases / 345 total tests; lint/format/types/build pass (`verification/MV-021/gate.log`). Graceful scanner failures write INSUFFICIENT/30; unsafe input 40, no defensible report 50, interrupt 130. No fault produced approval. PH-08 optional research deferred; continue PH-09 security/resources/CI.

- **2026-10-20:** MV-024 complete: 9 security / 354 total tests; lint/security rules/types pass (`verification/MV-024/gate-final.log`). Fixed filesystem case aliases using descriptor inode ancestry, cleaned remaining process-group descendants, rejected unknown scanner exits and missing complete-evidence producers. Remote/custom loader declarations remain unresolved instead of clean approval. OSV matched no advisories among 35 exact locked package/version pairs at query time; no safety guarantee. Next MV-025.

- **2026-10-20:** MV-025 complete: 8 targeted pass / 1 Linux memory-cap skip; 362 full-suite pass / 1 skip (`verification/MV-025/gate.log`). Measured 10,001 empty-file cap rejection 0.6571 s / 3,613,984 traced Python bytes; 1-second scanner timeout 1.0099 s. Project coverage including branch measurement: 91% combined, subprocess CLI execution not included in that instrumentation. Linux OS bounds remain unexecuted. Next MV-026 CI; hosted dispatch currently unavailable because gh has no authentication and no Linux runtime is installed.

- **2026-10-20 PH-09 local candidate checkpoint:** MV-026: 363 pass / 1 Linux-only skip, lock/lint/format/security/types/build pass; pinned Ubuntu/macOS workflow prepared and YAML parsed (`verification/MV-026/`). Real ModelScan 0.8.8 establishes standalone-file proof on macOS but scanner resources remain UNSUPPORTED/INSUFFICIENT. Hosted CI has NOT run; GitHub CLI lacks authentication, no Linux runtime available. User explicitly selected local candidate with hosted CI pending; proceed PH-10 local preparation without claiming public release readiness.

- **2026-10-20:** MV-027 complete: safe tutorial variants and controls executed with real CLI; 12 E2E / 364 total pass, one Linux-only skip, lint/types pass (`verification/MV-027/`). Current README and examples contain actual commands and source/claim/privacy/scanner limitations. Next MV-028 local candidate build/install under user-selected hosted-CI deferral.

- **2026-10-20:** MV-028 local candidate complete: 7 release tests / 371 total pass, one explicit Linux-only skip; lint/format/security/types pass (`verification/MV-028/gate.log`). Fresh wheel install has no editable checkout reference, six schemas/default policy/license included, actual CLI outcomes tested with runtime socket connections denied. Source archive includes documentation/examples/workflow and explicitly excludes operational verification notes; initial overly broad inclusion caught and fixed. Public release/hosted CI remain pending. Next MV-029 final claim/license/spec audit.

- **2026-10-20 PH-10 local candidate complete:** MV-029 final audit: 36 targeted / 381 full-suite pass, one Linux-only memory-cap skip; lock/lint/format/security rules/types (46 source files)/wheel+sdist build pass (`verification/PH-10/final-gate.log`). All 17 P0 requirements map to real tests; links/version/claim boundaries checked. Privacy regressions redact quoted/multiline and authorization values; original raw bytes remain sensitive and private. Initial Ruff S105 regex-name false positive is retained in final-gate-initial.log, corrected without changing redaction behavior. Dependency notices and point-in-time advisory evidence retained; no added dependencies. Final documentation/package verification and both distribution hashes are retained in `verification/PH-10/`. Hosted CI, Linux execution, project review, version-controlled checkpoint and publication remain pending by the selected scope; no benchmark or loader research run.

- **2026-10-20 PH-08 started:** MV-020 complete with 50 advisory tests / 434 full-suite pass, one Linux-only skip; lock/lint/format/security rules/mypy (47 source files) pass (`verification/MV-020/gate.log`). Combined advisory/CLI/fresh-install release selection: 77 pass (`targeted-final.log`). Exact PyPI enumerated-version matches are supplementary supplied-record assertions; stale/missing/partial/unsupported data cannot complete a required supplement. Output schema/digest binds report/artifact/snapshot/as-of identity and preserves the source admission report. No network client, version-range evaluator, dependencies, benchmark results or loader execution added. Initial formatting/type failures and successful reruns retained. Final documentation/build/package records and new artifact hashes are in `verification/MV-020/`; original PH-10 distributions preserved under ignored `dist/checkpoints/PH-10/`. Next unblocked task MV-022; hosted CI/public release/project review still pending.

- **2026-10-20 MV-022 development corpus implemented:** 28 targeted / 462 full-suite pass, one Linux-only skip; lint/types pass (`verification/MV-022/`). Ten inert recipes freeze generator/file/artifact identity, MIT provenance and development labels checked through alternative stdlib byte methods. Independent human review and hidden holdout are not supplied; the full benchmark research gate remains pending. Next: MV-023 development pilot, with no superiority claim.

- **2026-10-20 MV-023 local pilot/validation:** 60 targeted / 486 full-suite pass, one Linux-only skip; lock/lint/format/security/types (51 source files) pass. Fresh installed benchmark module runs with socket connections denied and an injected unavailable scanner; no completed result survives report failure/interruption. Real ModelScan 0.8.8 pilot on ten inert development cases, two repeats: 40 observations; six eligible joint input-context observations; fourteen baseline observations NOT_APPLICABLE. Outcome/policy/version tuples agree across 13 repeated eligible available groups, including unresolved outcomes. No efficacy/error rates or intervals are reported because independent adjudication and hidden holdout are absent. Complete private result/raw hashes and sanitized summary are retained; public study status INCONCLUSIVE.

- **2026-10-20 later-phase readiness:** Proposed PH-11 review packet prepared; read-only checks confirm Darwin arm64, no KVM device/Firecracker/jailer. No loader code or execution added. User explicitly selected **leave those gates pending; finish local validation** for independent benchmark/security review and a dedicated Linux/KVM host. PH-11 and public release remain gated. A newer external Git checkpoint af86ffee5c7b4f1e990e9dbbdba6625e973acef0 was observed during work; no agent commit/push/tag was performed, and subsequent changes are saved uncommitted.

- **2026-10-20 PH-12/MV-033 complete:** New local continuation adds raw-evidence verification; 22 targeted / 508 full-suite pass, one Linux-only skip; lock/lint/format/security/types pass (verification/MV-033/). Report byte pins and before/after checks, owner-path reads, bounded streaming raw hashes, missing/symlink/hardlink/FIFO/size/hash/drift and budget cases cannot falsely verify. New FR/task IDs extend the roadmap; external research/loader gates remain pending. Next MV-034.

- **2026-10-20 PH-13/MV-034 complete:** 13 targeted / 521 full-suite pass, one Linux-only skip; lock/lint/format/security/types (53 source files) pass (verification/MV-034/). Comparison distinguishes exact report bytes, raw declarations and semantic content, counts changed files/check groups and suppresses names/free text by default. Policy decisions are displayed as stored; no admission evaluation or raw-file authentication occurs. Explicit truncation, source drift and 0/30/40 CLI cases pass. Next MV-035.

- **2026-10-20 PH-14/MV-035 complete:** 29 batch / 558 full-suite tests pass, one Linux-only skip; lock/lint/format/security/types (54 source files) pass (verification/MV-035/). Explicit manifests retain all rows, share finite report/raw budgets and reject unsafe paths/drift. Captured report JSON is conservatively charged twice to reserve read/recheck work. A byte-verified INSUFFICIENT report remains INSUFFICIENT; audits never evaluate admission. 98 combined audit/CLI/fresh-install checks passed before final regressions; 33 batch/doc acceptance checks and the documented synthetic examples pass. Initial test-only import failure is retained. Final distribution/source identities and post-documentation verification are recorded in the same evidence directory. The user explicitly chose to extend the local plan; no dependencies, loader capability or accepted ADRs were added. All three requested local phases are complete; hosted CI, independent review/holdout, Linux/KVM, public release and PH-11 remain pending.

- **2026-10-20 hosted access restored:** User authorized GitHub CLI sign-in. Live Actions records show earlier Ubuntu/macOS runs failed on a cold offline runtime cache, correcting earlier no-hosted-run assumptions. MV-026 follow-up primes hash-locked dependencies during CI setup; a clean cache reproduces the failure and then passes 12 release/CI-contract cases after priming. Hosted rerun is pending; no platform/release/independent-review/loader gate is promoted. Evidence: verification/MV-026/hosted-followup/.
