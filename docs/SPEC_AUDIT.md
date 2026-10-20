# ModelVet blueprint specification audit

**Historical blueprint audit date:** 2026-10-20. **Historical scope:** Markdown/design consistency only. At that initial checkpoint no application code/tests/scanner had run. Later implementation evidence is recorded below; this historical table is not the current product state.

## Review outcome

| Check | Status | Evidence and remaining gap |
|---|---|---|
| Required docs | PASS (documentation) | All 21 requested Markdown files created, plus this audit file (22 total). |
| PRD completeness | PASS (draft coverage) | Requirements, scenarios, failure states, decision semantics, P0/P1/P2 distinction, example outputs and traceability included. Formal review pending. |
| Requirements traceability | PASS (document mapping) | 21 unique `FR-###`, each linked to implementation task `MV-###` and planned `T-...` test; no orphan requirement in static checker. Tests have not been created. |
| Architecture consistency | PASS (document mapping) | Component names aligned to file paths, Mermaid diagram and dependency direction. Unimplemented modules cannot be runtime-verified. |
| Stack verification | **PARTIAL** | Source-publication verified for uv 0.13.0, Typer 0.27.3, Pydantic 2.14.1 and Hypothesis 6.170.5; ModelScan README documents Python <=3.12. Actual combined lock resolution, build-backend pin, scanner version and compatibility tests pending MV-001/MV-010. |
| Security specification | PASS (documentation) | Threat model, trust boundaries, host non-execution rule, incomplete-evidence precedence, resource/sandbox prerequisites and residual risk register included. **No penetration/security execution test run.** |
| Roadmap executability | PASS (documentation) | 11 phases, explicit dependencies, effort ranges and go/no-go gates; P1 optional, P2 contingent. Actual estimates uncalibrated. |
| Task completeness | PASS (documentation) | 32 task cards include purpose, status, dependency, exact planned files/steps, test names, command pattern, acceptance and estimated effort. |
| Test/benchmark design | PASS (specification) | Safe-fixture matrix, independent ground truth, fair format eligibility, metrics and falsification criteria. **No benchmark corpus/results yet.** |
| Command accuracy | **PARTIAL** | CLI flags, exits and desired commands cross-linked; official ModelScan CLI flags documented; commands deliberately PLANNED/CONDITIONAL since no application exists. End-to-end command verification is impossible until implementation. |
| Progress accuracy | PASS | Every application phase/tasks NOT STARTED; no fabricated test success or results. |
| Source verification | **PARTIAL** | 20 primary-source records include direct URLs and caveats; HEAD references and commercial features may change; comparative runs and licenses unresolved. |
| Internal Markdown links | PASS (static) | Relative links point to existing documentation files after audit creation. |
| Local repository preservation | PASS | A new folder created; uploaded research was not changed; no Git project was available or overwritten. |

## Audit method and scope

Static analysis checked required-file existence, unique FR/task/phase IDs, requirement-to-task linkage, task-to-requirement references, test-ID presence, known dependencies, local relative links, and fenced-code balance. Missing mappings found in initial static check were corrected. The final audit record is maintained in this file; rerun checker or adopt a `tests/test_docs_contract.py` in future repository CI. No actual dependency resolution or source import took place.

## Open gaps to resolve before code

1. Approve or revise proposed ADR-001–ADR-012 with actual repository owner.
2. Lock exact compatible versions for hatchling, pytest, Ruff, mypy, pytest-cov and a tested ModelScan version (OQ-01).
3. Establish whether ModelScan reports positive per-file assessment proof; otherwise coverage must stay inconclusive (OQ-02).
4. Test snapshot size budgets and macOS/Linux process security assumptions (OQ-03/08/12).
5. Obtain fair baseline access/held-out corpus before asserting differentiated scanner-loader proof (OQ-10/13).
6. Decide whether separate microVM research is justified and supportable before starting PH-11 (OQ-09).

## Exact next task

**`MV-001` — Scaffold Python packaging and locked toolchain.** Create minimal `pyproject.toml`, `.python-version`, lockfile, ignore rules and package init; resolve pinned versions; install into an isolated Python 3.12 environment; run import/build smoke and record actual results in `PROGRESS.md`. The next task is **not started**.

## Implementation checkpoint — MV-001, 2026-10-20

The original blueprint audit above is historical. Packaging now exists, with a resolved lock, isolated wheel/sdist build, 3 passing smoke tests and saved dependency license/advisory review. `verification/MV-001/README.md` records the actual commands and failures. CLI, artifact pipeline, benchmark and microVM claims remain unimplemented. Next task: MV-002.

## Current implementation checkpoint — PH-03, 2026-10-20

MV-001–009 are complete with recorded task evidence. Final combined gate passes 140 tests, lint/format/types/lock/build on macOS (`verification/PH-03/final-gate.log`). Linux, scanner adapter, normalization/coverage, deterministic admission, reports, benchmark and isolation gates are still pending. MV-010 is next. Original blueprint-only audit statements above remain historical.

## Current implementation checkpoint — PH-04, 2026-10-20

MV-001–013 complete with macOS evidence. Final gate: 201 tests and lint/format/types/lock/build pass (`verification/PH-04/`). Original failed checks remain retained. No policy, report, full scan, Linux, benchmark or isolation gate is passed. Next unblocked task: MV-014.

## Current implementation checkpoint — PH-05, 2026-10-20

MV-001–015 complete on macOS with 287 tests and lock/lint/format/types/build evidence in `verification/PH-05/`. Policy validation works; deterministic evaluator rejects missing mandatory evidence and requires owned independent source-ban proof. The parser/default and five schemas survive fresh wheel installation with locked runtime dependencies. Full CLI scan/report generation, Linux/security/release gates, independent benchmarks and loader isolation remain pending. Next MV-016; prior checkpoints above are historical.

## Current implementation checkpoint — PH-10 local candidate, 2026-10-20

The conservative static CLI is implemented through all P0 local-candidate tasks. All 17 P0 FRs map to actual tests in tests/test_docs_contract.py. Final gate: 36 targeted and 381 full-suite tests pass, with one explicit Linux-only memory-cap skip; lock/lint/format/security rules/types/build pass on macOS (verification/PH-10/final-gate.log). Six packaged schemas, the default policy, license, examples and source archive boundaries are verified by fresh-install release tests. Unsupported archive proof and Darwin memory limits remain unresolved evidence; missing mandatory evidence cannot yield APPROVE or CONTROLS.

Documentation now describes actual commands, decision exits, privacy/semantic digest limits and local support evidence. Credential redaction is best effort; original raw bytes and exact filenames may contain sensitive data. Core/scanner dependency notices and point-in-time advisory review remain in verification/MV-001, MV-010 and MV-024. No new third-party dependencies were added during the final audit. Initial failures remain retained with successful reruns.

User-selected scope: **finish the local candidate; leave hosted CI pending**. Hosted Ubuntu/macOS CI has not run; Linux execution is unverified. ADRs remain Proposed and project review remains pending. No commit/tag/push/public release, independent security certification, PH-08 benchmark/advisory implementation or PH-11 model execution is claimed. Final commands, archive hashes and source whitespace review are recorded in verification/PH-10/; public gates remain in RELEASE_STATUS.md.

## Current optional P1 checkpoint — MV-020, 2026-10-20

The offline advisory supplement now has bounded input validation, a separate v1 schema and an explicit CLI; 50 advisory / 434 full-suite tests pass with one Linux-only skip. No policy/applicability version change or admission promotion occurs. Fresh installed-package checks exercise the actual supplement with socket connections denied. Snapshot source/completeness remain unauthenticated operator declarations; ranges/other ecosystems remain unresolved. Benchmark evidence and PH-11 prerequisites remain pending. Exact commands and builds are in verification/MV-020/. Original PH-10 records above remain historical candidate evidence.
