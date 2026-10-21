# Definition of done — task, milestone and release

**This document defines future gates, not passed checks.** Task/phase/release remains incomplete until evidence exists in `PROGRESS.md`.

## Task gate

- [ ] Implementation matches the task's named expected files, PRD requirement(s) and ADR constraints, with no unrelated features.
- [ ] Positive, negative, missing-evidence, malformed and timeout cases added as applicable; no model loading on host.
- [ ] Targeted test passes with actual command/date/commit/log; exit code captured.
- [ ] Broader applicable tests, lint and type checks pass or failures documented as blocking; no hand-waved exceptions.
- [ ] Security review: input bounds, path safety, stdout/stderr secrecy, status/result separation and policy fail-closed behavior considered.
- [ ] New dependency fully pinned in lock with license and vulnerability review; no forbidden dynamic imports or untrusted code execution.
- [ ] Code reviewed for readability, no incompatible schema changes, output deterministic as contract requires.
- [ ] README/spec/task docs and PROGRESS updated with the actual result, not intentions.

## Phase gate

Every phase task's DoD met; phase's explicit output from ROADMAP reproduced locally; no unaddressed critical security case; actual sources/versions captured; changes in assumptions recorded as ADR or open question. PH-08 baseline research can be incomplete without blocking the conservative static MVP, but **cannot** be cited as achieved.

## Release gate for v0.1 static MVP

- [ ] All P0 FR-001–FR-016 and FR-020 complete and mapped to passing test IDs (FR-017/018/019/021 remain separate).
- [ ] `APPROVE`, `CONTROLS`, `BLOCK`, `INSUFFICIENT` each tested with their policy rule trace; no mandatory gap can `APPROVE`.
- [ ] `uv sync --locked`, unit, property, integration and E2E checks, linter, mypy and build executed on documented supported OS; actual results retained.
- [ ] Snapshot mutation, symlink, special input, timeout, scanner no-supported, malformed output and unsupported format regression tests pass.
- [ ] No host `pickle.load`/`torch.load`/`from_pretrained` path on untrusted artifact; scanner subprocess environment and result limits reviewed.
- [ ] JSON v1 and Markdown reports documented and schema-validated; raw evidence traceable; private output and reproducibility tested.
- [ ] README includes exact scope, expected CLI usage, safe examples and *not a universal malware-free guarantee* disclaimer.
- [ ] Dependency and attribution checks documented; advisory source freshness and limitations reported honestly.
- [ ] End-to-end package install from built distribution; no fake outputs or benchmark claims.
- [ ] All unresolved high-severity risks explicitly accepted via review or release blocked.

## Evidence checklist record example (template, not actual)

```text
Task: MV-012
Commit: <real commit SHA>
Date / platform: <real timestamp and OS>
Targeted command: uv run pytest -q tests/test_coverage.py
Targeted exit/output: <actual>
Broad commands/exit: <actual>
Relevant fixture IDs: <actual>
Decision: COMPLETE / BLOCKED / NOT STARTED
Reviewed risks and unresolved issues: <actual>
```

## Block conditions

A passing green line-coverage number never substitutes for security behavior. Benchmark superiority, scanner-loader equivalence or isolation claims require separately reviewed experiments. No `P2` capability may be represented as released based on documentation or theoretical design alone.

## Local candidate checkpoint — 2026-10-20

The user selected local candidate completion with hosted CI pending. The local task evidence through MV-029 is recorded in PROGRESS and verification/PH-10: 381 tests pass, one Linux-only test is skipped, and lock/lint/format/security/types/build and fresh installation pass on macOS. This satisfies the selected local candidate scope. The unchecked public-release checklist above remains the release gate; hosted Linux/macOS execution, project review/risk acceptance and a version-controlled release checkpoint are pending. PH-08 and PH-11 are not achieved.

## Hosted static checkpoint — 2026-10-20

MV-026 now passes the declared Ubuntu 24.04/macOS 15 Intel hosted matrix; full tests, static gates, builds, fresh installation and real inert scanner contracts succeed at 3d24c0a (run 39465563101). Hosted target evidence is separate from local arm64. The release checklist still requires project review/residual-risk acceptance and publication; PH-08 independent holdout/adjudication and PH-11 dedicated host/isolation review are not satisfied by static CI. See RELEASE_REVIEW_PACKET.md for the concrete candidate and missing records.


## Current engineering completion — 2026-10-21

Static CLI and PH-12–17 extensions meet their recorded engineering/package acceptance gates. Run 39613283917 passes on Ubuntu 24.04/macOS 15 Intel at 767aa18. The original release checklist is a gate definition, not evidence that every box remains technically untested: P0 traceability, deterministic decisions, failure paths, schemas, docs, installed distributions and supported-target CI are implemented and verified in PROGRESS. Project/security residual-risk acceptance and publication remain pending. PH-08 independent research and all PH-11 loader prerequisites remain unsatisfied; no local test run substitutes for those external gates. See SPEC_AUDIT and RELEASE_REVIEW_PACKET for current dispositions.
