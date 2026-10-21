# ModelVet progress dashboard

**Updated 2026-10-21. Current delivery: Mac-first local static CLI and Workbench. MV-045 local arm64 and hosted Intel acceptance passed. Benchmark comparison and Linux/KVM loader research are deferred and no longer block the local Mac preview; engineering and honest mandatory-evidence checks remain required.** Earlier dated records below describe their original broader scope.

| Workstream | Actual state | Evidence |
|---|---|---|
| Product definition | Drafted, pending review | `../PRD.md` |
| Architecture and threat model | Drafted, pending review | `ARCHITECTURE.md`, `THREAT_MODEL.md` |
| Dependency resolution / lock | COMPLETE for foundation | `../pyproject.toml`, `../uv.lock`, `verification/MV-001/` |
| Source implementation | Full local CLI, static checks, evidence/coverage/policy, reports and packaging | `../src/modelvet/` |
| Tests/fixtures | 622 passed / one Linux-only skip locally; seven component and 14 browser workflows passed | `verification/workbench/PH-17-final-gate.log`, `verification/workbench/MV-044-final-browser.log` |
| Benchmarks | INCONCLUSIVE development pilot; independent research DEFERRED | `../benchmarks/results/`, `verification/MV-023/` |
| Isolated model-loading safety | DEFERRED | PH-11 / ADR-009 proposed |
| Release | MAC PREVIEW READY | Scoped local/internal acceptance passed; general-release certification is not claimed |

**Active task:** Mac preview engineering is complete; integrate and publish the scoped preview. PH-08 independent research and PH-11 remain deferred.

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
| PH-08 | LOCAL ENGINEERING IMPLEMENTED; independent research DEFERRED | MV-020 plus development corpus/pilot; no hidden holdout/independent adjudication |
| PH-09 | COMPLETE — tested hosted targets | MV-024–026; Ubuntu 24.04 + macOS 15 Intel hosted gate; local arm64 evidence separate |
| PH-10 | LOCAL CANDIDATE COMPLETE; public release PENDING | MV-027–029 verified; 381 pass / one Linux-only skip |
| PH-11 | DEFERRED — outside Mac preview | Proposed review packet prepared; no reviewed Linux/KVM environment |
| PH-12 | COMPLETE | Raw evidence verification; 508 pass / one Linux-only skip |
| PH-13 | COMPLETE | Stored report comparison; 521 pass / one Linux-only skip |
| PH-14 | COMPLETE | Explicit report batch audit; 558 pass / one Linux-only skip |
| PH-15 | COMPLETE locally | Optional dependencies, authenticated API, private worker/history |
| PH-16 | COMPLETE locally | Scan/report workspace, deterministic guidance, history/import/compare |
| PH-17 | PREVIEW COMPLETE; hosted Ubuntu/macOS passed | 622 Python tests, seven components, 14 browser workflows; installed wheel without Node/external socket access |
| PH-18 | COMPLETE — Mac preview engineering | MV-045; 627 Python tests, seven components, 15 browser workflows; hosted Mac gate passed |

## Decisions awaiting approval

`ADR-001` through `ADR-012` are **Proposed**. Priority: ADR-002 (Python+dependency choice), ADR-003 (snapshot budgets), ADR-005 (policy precedence), ADR-006 (external scanner), ADR-009 (no execution in MVP).

## Known risks / blockers

- ModelScan 0.8.8 named standalone-file coverage is observed and normalized. Archive/member completeness stays INCONCLUSIVE; Darwin memory enforcement is UNSUPPORTED required resource evidence.
- Core and separate pinned ModelScan environments pass local macOS and hosted Ubuntu checks. Broader platforms and dedicated loader isolation remain unverified.
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

- **2026-10-20 PH-09 hosted gate complete:** PR run 39465563101 at source 3d24c0a passes both Ubuntu 24.04 and macOS 15 Intel, including lint/format/security/types/full tests/build/fresh installation and the real inert scanner smoke. Ubuntu: 560 pass; macOS Intel: 559 pass / one Linux-only skip; local arm64: 559 pass / one Linux-only skip. ARM hosted jobs were queued and superseded, not counted as passing. The CI now tests pull requests and main pushes without redundant feature-branch push matrices. GitHub access is authenticated; no dependency/loader capability or ADR acceptance changed. PH-08 independent review/hidden holdout, PH-10 project/risk/public release and PH-11 dedicated Linux/KVM/review remain pending. Evidence: verification/MV-026/hosted-followup/.

- **2026-10-20 candidate refresh:** Final local gate passes 559 tests / one Linux-only skip, lock/lint/format/security/types and wheel/sdist build (verification/MV-026/hosted-followup/final-local-gate.log). Agent commits/pushes now exist on codex/ci-release-gates with PR 1; these changes correct hosted validation and prepare concrete review material. No public tag/package or loader execution is authorized by passing static CI alone. PH-08, PH-10 release acceptance and PH-11 remain dependent on the explicitly requested external records.

- **2026-10-20 PR/main comparison and push checkpoint:** PR 1 is merged as fbf603c1f471d932cc109a3da4350dbeddb724ab. Its checked head d440925 has exactly the same tree as merged main; freshly fetched local/remote main have zero commits ahead/behind before this evidence checkpoint. Post-merge run 39467012708 passes both hosted targets: Ubuntu 560 tests; macOS Intel 559 pass / one Linux-only skip; 10 release tests and real inert scanner contracts pass on each. The exact built wheel also installs with hash-locked cached dependencies and passes a network-denied synthetic scan plus stored-byte verification. Four remaining verification records were reviewed as structured metadata, with no artifact payload or credential data. Comparison, hashes and actual outputs are in verification/MV-026/hosted-followup/. This checkpoint changes progress/evidence only; no application code, dependency, accepted ADR, public release or loader capability changes.

- **2026-10-20 MV-011 contract correction:** Direct Python evidence construction accepted unpaired-surrogate object keys, which the pinned serializer changed into replacement characters. Twelve new regressions failed before the fix. Strict UTF-8 checks now cover keys in nested check details and dependency advisories; all 40 evidence tests pass, including 18 new Python/JSON/valid-Unicode cases. Full local gate: 577 pass / one Linux-only skip; lock/lint/format/security/types (54 source files), wheel/sdist build and 10 fresh installed-package checks pass. Evidence: `verification/MV-011/unicode-keys/`. No dependency/schema/policy change or demonstrated admission bypass. Hosted results for this correction are not inferred from the earlier baseline. Remaining work is independent release/research review and the gated Linux/KVM loader prerequisites.

- **2026-10-20 PH-15/MV-036:** Workbench contracts and optional dependency locks established; 9 contract/docs tests pass, Python/frontend combined import/request smoke passes. Exact pins, licenses and advisory queries recorded in verification/workbench/. The first npm attempt exposed a TypeScript 7/OpenAPI generator peer conflict; supported TypeScript 5.9.3 resolves without overrides. Workbench implementation now proceeds to MV-037; no new security or release approval is inferred.

- **2026-10-21 PH-15 complete:** MV-036–038 implement the optional authenticated loopback service, rooted folder/policy handling, fixed own-module scan worker, genuine stage events, cancellation/scanner cleanup, parent-death interruption and private SQLite history. Local gate: 599 passed / one Linux-only skip; lock/lint/format/security/types pass (64 source files). Worker tests cover all four decisions and CLI semantic parity; no model loading or report/policy schema change. Logs: verification/workbench/PH-15-gate.log and MV-038-tests.log. Next: MV-039 UI shell/scan setup.

- **2026-10-21 PH-16 complete:** MV-039–041 add the dark developer workbench, rooted scan setup, actual stage feedback, coverage matrix/file drill-down, safe record dialogs, deterministic guidance, private history, exact-byte JSON import/download, attachment verification and paged report comparison. Browser workflows cover every admission state, policy import and cancellation. Local full Python suite: 605 pass / one Linux-only skip; 7 frontend component tests and 6 Chromium workflows pass; types/build/lint/security pass. Desktop overview/report screenshots were inspected. Evidence: verification/workbench/MV-039 through MV-041 and PH-16-python-gate.log. PH-17 acceptance is next; public release remains pending independent review.


## MV-043 local packaging gate — 2026-10-21

Preserved external local commits 7691f1b/c314d5b before resuming. Added fresh optional-UI wheel installation and browser smoke, no Node on the application PATH, test-only nonloopback socket rejection in both server/worker environments, archive-content checks, generated-asset drift checks and pinned frontend Ubuntu/macOS CI steps. No admission/report schema change. Runtime third-party notices are bundled; frontend source/lock are in the sdist; modules and session state are excluded. Refreshed npm audit reports zero known matches, with every locked package carrying license metadata (see THIRD_PARTY).

Actual commands/results in verification/workbench: `uv run --extra ui pytest -q` → **620 passed / one Linux-only skip**, `MV-043-python.log`; installed/UI+CI contract subset → **6 passed**, `MV-043-installed.log`; frontend components → **7 passed**, `MV-043-components.log`; browser workflow → **13 passed**, `MV-043-browser.log`; Ruff/format/security/mypy65 source files/lock → passed, `MV-043-lint.log`. Format/type/build/schema/type generation passed. The initial installed tests had incorrect routes/headings and an unscoped badge count; failures are retained, corrected checks pass. Hosted execution of the extended workflow is pending; earlier static CI is not workbench CI evidence. Next MV-044.


## MV-044 / PH-17 local preview — 2026-10-21

Bundled four frozen, schema/digest-valid synthetic reports generated by the actual static engine (`tools/workbench_demos.py`), pinned by `workbench/demo/manifest.json`. Gallery is explicitly synthetic and does not add history; verification cannot imply supplied raw attachments. Added launch/private-session/scanner/recovery/installed-wheel instructions and the complete unknown-fixture correction/rerun/comparison tutorial in WORKBENCH_GUIDE. Updated CLI/architecture/stack/testing references and retained all 12 ADRs as Proposed. No model loading, automatic repair, dependency upgrade or admission/schema change.

Actual final commands: lock/Ruff/format/security/mypy65 files/schema drift passed; `uv run --extra ui pytest -q` → **622 passed / one Linux-only skip** (`PH-17-final-gate.log`); frontend format/type/seven component tests/type regeneration/build passed (`PH-17-final-frontend.log`); **14 Chromium workflows passed** (`MV-044-final-browser.log`), including measured responsive/axe and demo/history separation. Frozen demo/API subset passed twice, and installed-wheel acceptance validates demo assets plus real scans/import/compare/verify with the application PATH empty and external sockets rejected in the server/worker acceptance environment. The browser driver aborts external requests. A final strengthened installed-wheel browser check also starts a real scan through the folder picker and opens its saved history; all three installed UI tests passed (`PH-17-installed-final.log`). Initial selector failures and lint errors are retained; corrected gates passed. Starlette emits a development-only HTTPX TestClient deprecation warning; runtime/API tests pass with the locked stack, no forced dependency substitution.

Built wheel and source archive with `uv build --out-dir out/workbench-preview`; exact SHA-256 identities are retained in `verification/workbench/preview-distributions.json` after the final build. Operational logs/identities are excluded from the source archive; compiled assets/notices, demo reports, frontend sources/lock and test/build tools ship. Visual inspection of the 1440px Overview confirmed the labeled four-outcome gallery and private-history empty state; prior 375px report inspection remains recorded. This is a local preview, not a public release. Extended hosted execution is pending, as are independent project/security approval, hidden-holdout benchmark adjudication and the dedicated reviewed Linux/KVM loader gate.


## Hosted workbench acceptance — 2026-10-21

[Run 39611891146](https://github.com/HrshJha/ModelVet/actions/runs/39611891146) passed both targets at implementation commit `996d19f5af32ff1a89b770534e58e3c9d258a67a` in [PR 3](https://github.com/HrshJha/ModelVet/pull/3). Ubuntu 24.04: **623 Python tests passed**. macOS 15 Intel: **622 passed / one Linux-only skip**. Each target passed **seven component tests, 14 browser workflows, and the repeated 13-test core/UI installed-package subset**, plus lock/lint/types/generated-asset checks and build. Real ModelScan 0.8.8 inert standalone proof passed: Ubuntu records complete resource evidence and scoped APPROVE; macOS records unsupported memory evidence and INSUFFICIENT, as required. No malicious executable fixture or model load was used.

Exact GitHub step metadata is retained in `verification/workbench/hosted-results.json`, selected actual output in `hosted-summary.txt`, and full downloaded job logs in ignored `out/workbench-hosted/`, pinned by `hosted-log-pins.json`. The evidence follow-up changes documentation only; the linked run tested the implementation commit, not a future source state. PH-15–17 is complete as a local preview. All ADRs remain Proposed; independent project/security review, public publication approval, independent benchmark adjudication and dedicated Linux/KVM loader prerequisites remain pending. The local preview server uses generated synthetic input only; no operator model directory was selected.


## Whole-project completion audit — 2026-10-21

Rechecked the clean 767aa18 checkpoint, all 44 task cards, PR 3, final-head CI run 39613283917 and the release list. No unblocked incomplete P0 implementation task remains. PR 3 is open/mergeable, hosted checks pass, and no independent review approvals or published releases are recorded. Local capability checks still report Darwin arm64, no /dev/kvm, no Firecracker/jailer, and none of the checked Linux VM tools on PATH. Task MV-022/023 research acceptance and MV-030–032 loader prerequisites remain externally gated. No review/holdout/host evidence was supplied by the general completion request; the required inputs were requested while local auditing continued.

MV-029 documentation follow-up reconciles the current OPEN_QUESTIONS table, SPEC_AUDIT, CLI/data-model wording, security worker-boundary description and DoD interpretation with actual implemented/hosted evidence. Original dated checkpoints remain historical. No application code, dependencies, report/admission semantics, ADR status, release tag or loader capability changed. Exact audit snapshots and targeted doc-validation output are in verification/completion/. This records engineering completion without claiming the external release/research/loader gates have passed.


## Maintainer authorization to finalize integration — 2026-10-21

The maintainer explicitly authorized proceeding with all remaining available work. This authorizes candidate integration and local release preparation; it supplies no independent review identity, hidden holdout, dedicated host or containment observations. Preserve the existing external research/release/loader gates. The completion documentation follow-up passes 12 targeted contracts and Ruff; application code is unchanged from the verified 767aa18 checkpoint. Integrate the tested PR through the normal merge path without bypassing required checks, and retain source/package identities for review.


## MV-045 Mac-first scope change — 2026-10-21

The maintainer explicitly said only the Mac is available and instructed changing requirements that stop the current delivery. Work proceeds in an isolated main-based worktree because external commit 5f99293 on codex/evidence-unicode-keys tracks caches and omits the Workbench source. That commit is preserved untouched. FR-028/MV-045/PH-18 define the narrowed local Mac preview, defer PH-08 independent comparison and PH-11 loading, and replace Linux-host next-step guidance. The required hosted matrix now targets macOS 15 Intel, with local arm64 evidence separate. Engine/policy/evidence/report semantics and all security invariants remain unchanged. No dependency addition or independent validation claim.

Local acceptance: 17 targeted contracts and 627 full Python tests passed, with one Linux-only skip; Ruff/format/security/mypy65 files/lock/schema checks pass. Seven frontend component tests, formatting/type/build and 15 browser workflows pass. Exact outputs are retained under verification/mac-first/. The initial targeted check used a mismatched documentation phrase and failed; the wording was corrected and the full gate passed. The full suite includes fresh installed core/UI package acceptance. The changed copy and scope do not alter admission evidence or policy. Required hosted Mac execution is pending. Earlier research/review requirements remain documented for future broader work, not current product blockers.


## MV-045 Mac hosted acceptance — 2026-10-21

Run [39620134875](https://github.com/HrshJha/ModelVet/actions/runs/39620134875) passed the required macOS 15 Intel gate at a415a2ded7894c0ba603b0e40b2429f80ac08032. Exact platform counts and the real inert ModelScan observation are retained in verification/mac-first/hosted-summary.txt; complete step metadata/log pin are adjacent. Local arm64 acceptance passed 627 Python tests, one Linux-only skip, seven components and 15 browser workflows, plus lock/lint/types/schema/build/fresh-install tests. An actual installed-wheel browser session also selected the generated synthetic folder and produced a scoped APPROVE with 9/9 mandatory checks; no trained model was loaded. Mac capability text was visually inspected. ModelScan's required Darwin resource gap remains INSUFFICIENT in its real smoke contract.

MV-045 is complete for the narrowed Mac preview; no Linux/KVM host or independent benchmark is a prerequisite. This is internal engineering validation, not independent certification. Source/guidance changes preserve default policy/evidence/coverage files exactly. The following evidence-only update does not change the tested application. Prepare the prerelease with exact merged-source/package identities; repository visibility is unchanged. Preserved external branch/commit 5f99293 is not part of this release.


## Mac release source hygiene — 2026-10-21

While PR 5 was under validation, external PR 4 merged 5f99293 into main, tracking generated frontend dependencies and test-session files. PR 5's merge 8d3e32b includes that unrelated change even though its application code matches the passing Mac preview. Preserve the original user branch/commit and working files; remove generated node_modules/test-results from the release index, keeping the existing ignore rules. Add a Git-index regression so future CI rejects tracked dependency caches and browser state. No application code or operator artifacts are removed. This supersedes the earlier statement that external 5f99293 was absent from the merge; its history is preserved, while generated files are excluded from the release tree. Revalidate packaging from the clean tree before publishing the Mac preview.

Actual hygiene validation: Ruff lint/format and the full suite pass: **628 passed / one Linux-only skip** (`verification/mac-first/hygiene-full.log`). The 18-test Mac/package contract subset and 13 repeated installed core/UI checks pass; fresh wheel/sdist build succeeds. Generated dependency and browser-session files are absent from the index; the original external commit and working files remain intact. Required hosted Mac validation of this cleanup follows in its own PR before publication.
