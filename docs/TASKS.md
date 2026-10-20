# Executable implementation backlog

**As of 2026-10-20 P0 tasks through MV-029 are complete for the local candidate. Hosted Ubuntu/macOS verification passes; public release remains pending; PH-08/MV-020 is complete; MV-022/023 local development engineering is implemented with independent research gates PENDING; gated PH-11 execution tasks are NOT STARTED.** PH-12–14 local report audits are complete with evidence in verification/MV-033 through MV-035. Task IDs stable; completion means implementation + test evidence + updated PROGRESS, never existence of planned filename alone. **Scheduling order follows P0 phase dependencies rather than numeric task IDs**: MV-021 (PH-07/P0) precedes optional MV-020 (PH-08/P1) in the recommended release path. There is no remaining local-candidate P0 implementation task in the selected scope. Task estimates are focused hours, not time-to-delivery promises. Command patterns remain planned until their task evidence records successful execution.

## Backlog index

| Task | Title | Priority | Phase | Requirements | Depends on | Est. |
|---|---|---|---|---|---|---|
| MV-001 | Scaffold Python packaging and locked toolchain | P0 | PH-01 | FR-014 | none | 5–8 h |
| MV-002 | Wire CLI help, output and status skeleton | P0 | PH-01 | FR-014 | MV-001 | 3–4 h |
| MV-003 | Validate local input and output separation | P0 | PH-02 | FR-001 | MV-001 | 4–6 h |
| MV-004 | Implement bounded safe discovery and snapshot | P0 | PH-02 | FR-002 | MV-003 | 7–10 h |
| MV-005 | Compute canonical file and manifest identity | P0 | PH-02 | FR-003,FR-015 | MV-004 | 6–10 h |
| MV-006 | Implement bounded format classifier | P0 | PH-02 | FR-004 | MV-005 | 5–8 h |
| MV-007 | Build non-executing structural inspectors | P0 | PH-03 | FR-005 | MV-006 | 7–10 h |
| MV-008 | Collect declared provenance/license evidence | P0 | PH-03 | FR-006 | MV-005 | 4–7 h |
| MV-009 | Read explicit pinned dependency manifest | P0 | PH-03 | FR-007 | MV-005 | 5–8 h |
| MV-010 | Implement ModelScan CLI adapter | P0 | PH-04 | FR-008 | MV-001,MV-004 | 7–12 h |
| MV-011 | Define typed evidence models and normalizer | P0 | PH-04 | FR-009 | MV-005,MV-010 | 5–8 h |
| MV-012 | Reconcile per-file required check coverage | P0 | PH-04 | FR-010 | MV-006,MV-011 | 6–10 h |
| MV-013 | Detect metadata and evidence conflicts | P0 | PH-04 | FR-011 | MV-008,MV-011 | 4–6 h |
| MV-014 | Implement deterministic four-state evaluator | P0 | PH-05 | FR-012 | MV-012,MV-013 | 8–12 h |
| MV-015 | Parse and validate policy TOML | P0 | PH-05 | FR-012 | MV-014 | 6–10 h |
| MV-016 | Produce schema-valid JSON and Markdown reports | P0 | PH-06 | FR-013 | MV-011,MV-014 | 7–11 h |
| MV-017 | Verify repeatability and post-scan drift | P0 | PH-06 | FR-015 | MV-005,MV-016 | 5–8 h |
| MV-018 | Complete doctor/inspect/version CLI commands | P0 | PH-06 | FR-020,FR-014 | MV-002,MV-016 | 4–7 h |
| MV-019 | Add safe fixtures and end-to-end scan acceptance | P0 | PH-07 | FR-016 | MV-016,MV-018 | 6–10 h |
| MV-020 | Support local advisory snapshot enrichment | P1 | PH-08 | FR-019 | MV-009 | 5–8 h |
| MV-021 | Complete fail-closed fault injection matrix | P0 | PH-07 | FR-016 | MV-019 | 4–8 h |
| MV-022 | Implement benchmark corpus and ground truth manifest | P1 | PH-08 | FR-017 | MV-019 | 8–14 h |
| MV-023 | Run fair baseline comparison and result audit | P1 | PH-08 | FR-017 | MV-022,MV-010 | 7–12 h |
| MV-024 | Review security-sensitive code and dependencies | P0 | PH-09 | FR-002,FR-008 | MV-019 | 5–9 h |
| MV-025 | Stress test resource/path boundaries | P0 | PH-09 | FR-002,FR-005 | MV-021 | 6–10 h |
| MV-026 | Implement CI and supported-platform verification | P0 | PH-09 | FR-014,FR-016 | MV-024,MV-025 | 5–9 h |
| MV-027 | Produce tutorial examples and reproducibility guide | P0 | PH-10 | FR-013,FR-014 | MV-019 | 4–7 h |
| MV-028 | Build distribution and public release candidate | P0 | PH-10 | FR-014 | MV-026,MV-027 | 4–7 h |
| MV-029 | Audit licenses, docs, specifications and claims | P0 | PH-10 | FR-006,FR-017 | MV-028 | 2–4 h |
| MV-030 | Design and independently review isolated loader runner | P2 | PH-11 | FR-018 | MV-023,MV-029 | 15–30 h |
| MV-031 | Implement scoped version-specific loader test | P2 | PH-11 | FR-021 | MV-030 | 12–25 h |
| MV-032 | Independently adjudicate discrepancy findings | P2 | PH-11 | FR-018,FR-021 | MV-031 | 8–15 h |
| MV-033 | Verify stored raw evidence | P1 | PH-12 | FR-022 | MV-016 | not calibrated |
| MV-034 | Compare stored reports | P1 | PH-13 | FR-023 | MV-033 | not calibrated |
| MV-035 | Audit an explicit report batch | P1 | PH-14 | FR-024 | MV-033,MV-034 | not calibrated |

## Detailed task cards (normative)


### MV-001 — Scaffold Python packaging and locked toolchain

- **Priority / status / phase:** P0; **COMPLETE**; `PH-01`. **Requirement(s):** FR-014. **Estimated focused effort:** 5–8 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** none; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `pyproject.toml`, `.python-version`, `uv.lock`, `.gitignore`, `src/modelvet/__init__.py`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Create Python 3.12 package metadata and Typer/Pydantic runtime dependency pins; resolve hatchling/pytest/ruff/mypy and record versions; run import/build smoke; record license inventory and commands. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_import_smoke.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv lock --check && uv sync --locked && uv run python -c "import typer, pydantic" && uv build`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** `uv sync --locked` + isolated `uv build` work without scanner dependency; report actual versions. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Verification (2026-10-20):** required lock/sync/import/build chain exit 0; 3 packaging tests passed; lint, format, mypy and dependency consistency passed on macOS arm64/Python 3.12.15. License and advisory review retained in `verification/MV-001/README.md`. Base commit `e2f2bb2`; working changes uncommitted. No scanner or CLI implemented.

### MV-002 — Wire CLI help, output and status skeleton

- **Priority / status / phase:** P0; **COMPLETE**; `PH-01`. **Requirement(s):** FR-014. **Estimated focused effort:** 3–4 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-001; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `src/modelvet/cli/main.py`, `tests/test_cli.py`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Implement scan/inspect/policy validate/doctor/version command signatures as safe placeholders; implement exit enums; reject fake scan success; stderr vs stdout behavior; NO_COLOR handling. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_cli.py::test_help_and_exit_contract`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_cli.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** CLI help matches spec and incomplete scan cannot return 0. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Verification (2026-10-20):** 21 CLI tests and 24 full-suite tests pass; lint/format, mypy, lock and isolated build exit 0. Logs: `verification/MV-002/`. Incomplete operations return 50 with no decision. Initial exception-import failures retained.

### MV-003 — Validate local input and output separation

- **Priority / status / phase:** P0; **COMPLETE**; `PH-02`. **Requirement(s):** FR-001. **Estimated focused effort:** 4–6 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-001; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `src/modelvet/inventory/gate.py`, `tests/test_input_gate.py`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Resolve path policy without following symlinks; validate existing directory, readability and independent report location; report usage failures with typed errors. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_input_gate.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_input_gate.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** Path traversal, output overlap and missing directory all rejected. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Verification (2026-10-20):** 15 input-gate tests and 39 suite tests passed; lint and mypy pass after explicit dataclass default narrowing. Logs: `verification/MV-003/`. No input/output file writes; symlink ancestors opened with directory FDs and O_NOFOLLOW; reviewed ceilings cannot be raised.

### MV-004 — Implement bounded safe discovery and snapshot

- **Priority / status / phase:** P0; **COMPLETE**; `PH-02`. **Requirement(s):** FR-002. **Estimated focused effort:** 7–10 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-003; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `src/modelvet/core/snapshot.py`, `src/modelvet/inventory/discover.py`, `tests/test_snapshot.py`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Walk with lstat and no symlink follow, reject special/hardlinked nodes and excessive files; copy bounded bytes to private dir; guarantee cleanup in finally; enforce combined budget. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_snapshot.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_snapshot.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** No special file read, cap bypass or retained snapshot after normal/failed run. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Verification (2026-10-20):** 17 snapshot tests, 56 total tests; lint/types pass. Logs: `verification/MV-004/`. Descriptor-based streaming copies reject special/hardlinked nodes, detect tested mutations, enforce byte/entry/depth caps and clean temporary roots on success and errors.

### MV-005 — Compute canonical file and manifest identity

- **Priority / status / phase:** P0; **COMPLETE**; `PH-02`. **Requirement(s):** FR-003,FR-015. **Estimated focused effort:** 6–10 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-004; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `src/modelvet/inventory/identity.py`, `tests/test_identity.py`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Stream hash each snapshot file; normalize/sort paths; derive manifest-v1 digest and stable IDs; rehash source after scan; expose drift outcome. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_identity.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_identity.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** Deterministic across traversal order; one changed byte changes digest; mutation refuses approval. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Verification (2026-10-20):** 11 identity tests, including Hypothesis order/content properties; 67 suite tests, lint/types pass. Logs: `verification/MV-005/`. Source rechecks stream hashes without a second on-disk copy; snapshot additions/changes and tested source mutations refuse stable identity.

### MV-006 — Implement bounded format classifier

- **Priority / status / phase:** P0; **COMPLETE**; `PH-02`. **Requirement(s):** FR-004. **Estimated focused effort:** 5–8 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-005; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `src/modelvet/inventory/classify.py`, `tests/test_classify.py`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Detect safetensors, ZIP/PyTorch patterns, pickle-like, config/documentation, Python source and unknown; cross-check suffix vs signature; derive applicability; unknown relevant data cannot silently be not-applicable. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_classify.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_classify.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** All sample formats classed; suspicious mismatch and unknown trigger explicit status. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Verification (2026-10-20):** 14 classifier tests, 81 suite tests; lint/format, mypy, lock and isolated build pass. Logs: `verification/MV-006/`. Unknown/mismatched formats remain explicit; reads are bounded and symlink-resistant. PH-02 gate passed on macOS, not independently on Linux.

### MV-007 — Build non-executing structural inspectors

- **Priority / status / phase:** P0; **COMPLETE**; `PH-03`. **Requirement(s):** FR-005. **Estimated focused effort:** 7–10 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-006; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `src/modelvet/structural/safetensors.py`, `src/modelvet/structural/zip_index.py`, `tests/test_structural.py`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Parse at most bounded safetensors header, reject invalid UTF-8/duplicate keys/offsets; enumerate ZIP central directory without extracting, reject path escapes and duplicate entries; never deserialize. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_structural.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_structural.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** Malformed header/ZIP yield explicit check failure; no arbitrary imports or decompression. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Verification (2026-10-20):** 32 structural/strict-JSON tests; 113 total, lint/types pass (`verification/MV-007/`). Bounded safetensors offsets and classic ZIP local/central consistency checks implemented without extraction/loading. Unsupported ZIP features/dtypes remain explicit.

### MV-008 — Collect declared provenance/license evidence

- **Priority / status / phase:** P0; **COMPLETE**; `PH-03`. **Requirement(s):** FR-006. **Estimated focused effort:** 4–7 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-005; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `src/modelvet/metadata/claims.py`, `tests/test_claims.py`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Read only bounded local README/LICENSE/JSON, preserve field/source/path/line; do not infer training data rights; emit missing claims and contradiction candidates. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_claims.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_claims.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** Opposing licenses both preserved; missing evidence explicit; raw source hash recorded. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Verification (2026-10-20):** 11 metadata tests; 124 total, lint/types pass (`verification/MV-008/`). Missing kinds explicit; conflicting declarations preserved with exact file hashes/pointers; no model-code import or legal verification.

### MV-009 — Read explicit pinned dependency manifest

- **Priority / status / phase:** P0; **COMPLETE**; `PH-03`. **Requirement(s):** FR-007. **Estimated focused effort:** 5–8 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-005; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `src/modelvet/dependencies/manifest.py`, `tests/test_dependencies.py`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Validate user-supplied local dependency list name/ecosystem/version; record source hash and absence; reject unpinned versions for version-based security claim; do not query network. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_dependencies.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_dependencies.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** Malformed/unknown versions yield INCONCLUSIVE records; not false no-vulnerability. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Verification (2026-10-20):** 15 dependency-manifest tests, 139 total; lint/format/types/lock/build pass (`verification/MV-009/`). Explicit exact pins remain claims; absent, malformed, unsupported and conflicting versions remain unresolved. PH-03 complete on macOS only.

### MV-010 — Implement ModelScan CLI adapter

- **Priority / status / phase:** P0; **COMPLETE**; `PH-04`. **Requirement(s):** FR-008. **Estimated focused effort:** 7–12 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-001,MV-004; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `src/modelvet/scanners/base.py`, `src/modelvet/scanners/modelscan.py`, `tests/test_modelscan_adapter.py`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Pin tested modelscan version; subprocess shell=False on snapshot only, env allowlist and timeouts; capture JSON+stderr hash; map documented 0–4 exits and unsupported cases; verify observed version. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_modelscan_adapter.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_modelscan_adapter.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** All 5 exit cases and timeout/malformed report tested with fake executable, no host code load. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Verification (2026-10-20):** 17 adapter contract tests (exit 0/1/2/3/4, malformed/missing/oversized/symlink reports, version/missing tool, skips, timeout/output caps, environment/limits and artifact-supplied executable rejection). 157 suite tests, lint/format/types and both environment consistency checks pass. Real pinned ModelScan 0.8.8 inert fixture smoke passed. Logs: `verification/MV-010/`; macOS memory-limit gap remains explicit and requires unresolved resource coverage.

### MV-011 — Define typed evidence models and normalizer

- **Priority / status / phase:** P0; **COMPLETE**; `PH-04`. **Requirement(s):** FR-009. **Estimated focused effort:** 5–8 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-005,MV-010; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `src/modelvet/evidence/models.py`, `src/modelvet/evidence/normalize.py`, `tests/test_evidence.py`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Implement v1 Pydantic schemas and normalization; preserve raw digest/tool/version/input hash; keep execution status separate from findings; unknown records fail closed. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_evidence.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_evidence.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** Schema validates; empty findings on FAILED never mapped to NO_FINDINGS. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Verification (2026-10-20):** 21 schema/normalization tests; 178 total; lint/format/types/lock/build pass. Real ModelScan JSON normalization smoke passes, with named standalone coverage COMPLETE and macOS resource coverage UNSUPPORTED. Raw hashes retained; unsupported/unknown/invalid evidence never becomes NO_FINDINGS. Logs: `verification/MV-011/`.

**Unicode-key follow-up (2026-10-20):** Reopened the existing UTF-8 contract after direct Python construction accepted invalid object keys. Twelve regression cases failed before the correction; all 40 evidence tests now pass, including 18 added Python/JSON/valid-Unicode cases. Full local gate: 577 passed / one Linux-only skip; lock, lint, formatting, security lint, types, build and 10 installed-package release tests pass. Key validation covers nested check details and dependency advisories; schema/lock unchanged. Logs: `verification/MV-011/unicode-keys/`. Task remains COMPLETE; independent release/loader gates remain pending.

### MV-012 — Reconcile per-file required check coverage

- **Priority / status / phase:** P0; **COMPLETE**; `PH-04`. **Requirement(s):** FR-010. **Estimated focused effort:** 6–10 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-006,MV-011; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `src/modelvet/coverage/reconciler.py`, `tests/test_coverage.py`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Create expected (file,check) pairs from applicability; join normalized outcomes; classify completed/skipped/failed/unsupported/inconclusive; no positive proof -> INCONCLUSIVE. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_coverage.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_coverage.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** Partial archive/skips cannot be clean, duplicate contradictory results fail closed. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Verification (2026-10-20):** 13 coverage tests, 191 total; lint/format/types/lock/build pass (`verification/MV-012/`). Every expected pair has one disjoint terminal bucket. Missing/duplicate/contradictory/mismatched evidence stays unresolved; optional gaps remain visible. Registry expectations do not trust producer check lists.

### MV-013 — Detect metadata and evidence conflicts

- **Priority / status / phase:** P0; **COMPLETE**; `PH-04`. **Requirement(s):** FR-011. **Estimated focused effort:** 4–6 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-008,MV-011; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `src/modelvet/coverage/conflicts.py`, `tests/test_conflicts.py`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Detect inconsistent license/provenance declarations and scanner+status contradictions; preserve both sources and mark decision relevance. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_conflicts.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_conflicts.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** Conflict records stable and never silently select first source. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Verification (2026-10-20):** 9 conflict tests; final PH-04 suite 201 passed, lint/format/types/lock/build exit 0 (`verification/PH-04/final-gate.log`). Source claims remain preserved; ordering cannot select a favorable observation. Initial type and nested-NaN failures are retained with their corrections.

### MV-014 — Implement deterministic four-state evaluator

- **Priority / status / phase:** P0; **COMPLETE**; `PH-05`. **Requirement(s):** FR-012. **Estimated focused effort:** 8–12 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-012,MV-013; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `src/modelvet/policies/evaluator.py`, `tests/test_policy.py`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Evaluate corroborated bans, required evidence completeness, named controls and approvals with fixed precedence; include rule IDs/reasons; never invoke LLM. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_policy.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_policy.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** Exhaustive status/property tests show no APPROVE/CONTROLS with mandatory gaps. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Actual verification (2026-10-20):** 27 targeted tests, including 1,296 status combinations under plain and controlled policies; 228 full-suite tests passed. Ruff and mypy (37 source files) pass. Logs: `verification/MV-014/`. Typed policy/decision contracts were introduced here because the evaluator needs them; TOML parsing/defaults remain MV-015. No dependency or lock change.

### MV-015 — Parse and validate policy TOML

- **Priority / status / phase:** P0; **COMPLETE**; `PH-05`. **Requirement(s):** FR-012. **Estimated focused effort:** 6–10 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-014; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `src/modelvet/policies/models.py`, `src/modelvet/core/config.py`, `tests/test_policy_config.py`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Define v1 mandatory applicability, prohibited categories and control schema; tomllib parse, reject unknown keys/ambiguous rules; embed conservative default. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_policy_config.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_policy_config.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** Contradictory/unknown policy rejected; policy hash stable. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Actual verification (2026-10-20):** 58 policy/config tests passed, including malformed/oversized/deep TOML, ambiguous rules, owner/unknown-control checks, unsafe files, drift, semantic identity and CLI success/error paths. Final PH-05 gate: 287 total tests; lock/lint/format/mypy/build all pass. Fresh locked-runtime wheel install loads the packaged default and all five schema resources. Evidence: `verification/MV-015/`, `verification/PH-05/`. Initial parent-symlink failure retained and fixed. No new dependencies. Policy validation is wired here because it directly exercises this parser; remaining report/doctor/scan integration stays in later tasks.

### MV-016 — Produce schema-valid JSON and Markdown reports

- **Priority / status / phase:** P0; **COMPLETE**; `PH-06`. **Requirement(s):** FR-013. **Estimated focused effort:** 7–11 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-011,MV-014; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `src/modelvet/reports/json_report.py`, `src/modelvet/reports/markdown.py`, `src/modelvet/reports/writer.py`, `tests/test_reports.py`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Render traceable sections, semantic digest, limitations and redacted paths; write atomic non-overwriting output outside input, validate schema before save. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_reports.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_reports.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** No dangling evidence refs; strict JSON; MD escaped; limited permissions. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Actual verification:** `verification/MV-016/gate.log`: 19 report tests / 306 full-suite tests, lint and strict types pass on macOS. Added report-v1 schema, semantic digest, reference index, escaped Markdown, redaction and descriptor-based private non-overwriting writes; no dependencies added.

### MV-017 — Verify repeatability and post-scan drift

- **Priority / status / phase:** P0; **COMPLETE**; `PH-06`. **Requirement(s):** FR-015. **Estimated focused effort:** 5–8 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-005,MV-016; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `src/modelvet/core/snapshot.py`, `src/modelvet/reports/json_report.py`, `tests/test_reproducibility.py`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Rehash initial source after evaluation, separate run timestamp from semantic digest; introduce source mutation; assert no stale clean report. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_reproducibility.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_reproducibility.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** Frozen input yields same semantic digest; mutation triggers INSUFFICIENT. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Actual verification:** `verification/MV-017/gate.log`: 8 repeatability/drift tests / 314 total, lint/types pass. Final source/snapshot rehash invalidates identity and independent ban proof on changes; raw observation metadata is excluded from semantic content.

### MV-018 — Complete doctor/inspect/version CLI commands

- **Priority / status / phase:** P0; **COMPLETE**; `PH-06`. **Requirement(s):** FR-020,FR-014. **Estimated focused effort:** 4–7 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-002,MV-016; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `src/modelvet/cli/main.py`, `tests/test_doctor.py`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Probe scanner/version without executing model; inspect strict reports; version schema support, noninteractive output and exit contract. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_doctor.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_doctor.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** Doctor missing scanner reports availability rather than success; inspect invalid report fails 40. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Actual verification:** `verification/MV-018/gate.log`: 5 doctor/inspect tests / 317 total; lint/types/build pass. Doctor distinguishes diagnostic success from scanner readiness; inspect validates stored schema/digest without rescanning; version advertises v1. PH-06 complete locally.

### MV-019 — Add safe fixtures and end-to-end scan acceptance

- **Priority / status / phase:** P0; **COMPLETE**; `PH-07`. **Requirement(s):** FR-016. **Estimated focused effort:** 6–10 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-016,MV-018; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `tests/fixtures/`, `tests/test_e2e.py`, `examples/default.toml`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Generate only small non-executable benign/malformed/unsupported fixtures; run CLI via subprocess; verify JSON/MD, hashes, decisions, exits, no imports of model code. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_e2e.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_e2e.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** E2E covers all four states and missing mandatory evidence with real CLI. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Actual verification:** `verification/MV-019/gate.log`: 11 real CLI E2E cases / 327 total; lint/types pass. Application service orchestrates static checks, scanner evidence, final identity, decisions and reports. All four decisions and three output modes verified on safe synthetic fixtures.

### MV-020 — Support local advisory snapshot enrichment

- **Priority / status / phase:** P1; **COMPLETE**; `PH-08`. **Requirement(s):** FR-019. **Estimated focused effort:** 5–8 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-009; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `src/modelvet/dependencies/advisories.py`, `tests/test_advisories.py`, supplemental CLI, `schemas/advisories-v1.json`, `docs/ADVISORY_SPEC.md`, safe examples. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Accept explicit OSV-format local input, validate timestamp/version/ecosystem; distinguish affected-version from exploitability; stale/absent feed inconclusive if mandatory. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_advisories.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_advisories.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** Version matching reproducible offline; no implicit network. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Actual verification:** `verification/MV-020/gate.log`: 50 advisory tests / 434 total pass, one Linux-only skip; lock/lint/format/security/types pass. `targeted-final.log`: 77 advisory/CLI/fresh-install release cases pass, including runtime socket-denial guard and source-report preservation. The supplementary command requires explicit UTC evaluation time and local query-scoped snapshot input; stale/missing/partial/unsupported semantics stay unresolved. Only exact enumerated PyPI versions are matched; no network or dependency addition. Static policy v1 and existing admission reports are not changed. Full interface and scope reduction: ADVISORY_SPEC.md.

### MV-021 — Complete fail-closed fault injection matrix

- **Priority / status / phase:** P0; **COMPLETE**; `PH-07`. **Requirement(s):** FR-016. **Estimated focused effort:** 4–8 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-019; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `tests/test_fail_closed.py`, `tests/fixtures/`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Inject scanner exit2/3/4, timeouts, unreadable file, JSON corruption, output IO failure, conflicts and interrupt; assert correct 30/40/50/130 exit distinction. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_fail_closed.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_fail_closed.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** No fault yields false APPROVE; reports on graceful errors wherever possible. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Actual verification:** `verification/MV-021/gate.log`: 18 fault tests / 345 total; lint/format/types/build pass. Scanner exits, timeout, output overflow, absent/malformed/skipped/conflicting proof, version/unavailability, source drift, output failure, unreadable input and interruption fail without false approval.

### MV-022 — Implement benchmark corpus and ground truth manifest

- **Priority / status / phase:** P1; **IMPLEMENTED — development corpus; independent holdout/review PENDING**; `PH-08`. **Requirement(s):** FR-017. **Estimated focused effort:** 8–14 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-019; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `benchmarks/manifest.json`, `benchmarks/README.md`, `tests/test_benchmark_manifest.py`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Define independently verified non-executable labeled benign/malformed/adversarial-reference cases; keep holdout hidden; document licenses/provenance; build manifest parser. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_benchmark_manifest.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_benchmark_manifest.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** No invented ground truth or unsafe fixtures in regular test suite. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Actual local verification:** `verification/MV-022/task.log`: 28 manifest cases pass; gate.log: 462 full-suite pass / one Linux-only skip, lint/types pass. Ten closed inert recipes have reproducible file/artifact hashes and alternative stdlib byte-method labels. No hidden corpus or independent human adjudication is claimed; manifest explicitly refuses such labels. Corpus engineering supports a development pilot in MV-023; the research acceptance gate remains pending external holdout/review.

### MV-023 — Run fair baseline comparison and result audit

- **Priority / status / phase:** P1; **IMPLEMENTED — local pilot; independent research acceptance PENDING**; `PH-08`. **Requirement(s):** FR-017. **Estimated focused effort:** 7–12 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-022,MV-010; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `benchmarks/results/`, `docs/BENCHMARK_PLAN.md`, `tests/test_benchmark_metrics.py`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Implement comparison respecting supported format/tool versions; independently adjudicate findings; report false-clean, support and overhead with intervals; publish inconclusive if inadequate data. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_benchmark_metrics.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_benchmark_metrics.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** Unsupported baseline excluded rather than counted failure; raw experiment metadata retained. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Actual local verification:** `verification/MV-023/targeted.log`: 60 corpus/metrics/fresh-install release cases pass. Final gate: 486 total pass / one Linux-only skip, lock/lint/format/security/types pass. Real pinned ModelScan 0.8.8 pilot: ten inert cases, two repeats, 40 observations; six eligible joint input-context observations, fourteen baseline NOT_APPLICABLE observations. All results remain INCONCLUSIVE. No reviewed discrepancy positives or hidden holdout exist; efficacy/error rates/intervals remain null. Alternative tools are NOT_RUN, not penalized. Private raw metadata/reports retained in ignored out/development-pilot-20261020; sanitized summary in benchmarks/results. User explicitly selected leaving independent review/Linux prerequisites pending and finishing local validation. This does not complete the PH-08 research gate or unlock PH-11.

### MV-024 — Review security-sensitive code and dependencies

- **Priority / status / phase:** P0; **COMPLETE**; `PH-09`. **Requirement(s):** FR-002,FR-008. **Estimated focused effort:** 5–9 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-019; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `docs/SECURITY_POLICY.md`, `pyproject.toml`, `uv.lock`, `tests/test_security_invariants.py`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Inspect imports and subprocess launch for dangerous loader calls/shell; audit lock and output permissions; run static security lint; add regression checks. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_security_invariants.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_security_invariants.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** No host model execution, no shell, no unsafe output path. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Actual verification:** `verification/MV-024/gate-final.log`: 9 security tests / 354 total; Ruff security rules, lint and types pass. Inode ancestry closes case-alias output/staging/scanner gaps; normal exit kills remaining group children; report producers and unknown exits validated. 35 locked package/version pairs queried at OSV with zero matches; 30 core license metadata records and prior scanner notices reviewed. This is an internal review, not independent certification.

### MV-025 — Stress test resource/path boundaries

- **Priority / status / phase:** P0; **COMPLETE**; `PH-09`. **Requirement(s):** FR-002,FR-005. **Estimated focused effort:** 6–10 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-021; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `tests/test_resource_limits.py`, `tests/test_snapshot.py`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Test many paths, huge declared sizes, nested malformed headers, symlink races where testable; assert bounded reads, explicit fail-closed outcomes. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_resource_limits.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_resource_limits.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** Wall-time/memory budgets observed in tests, no process runaway. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Actual verification:** `verification/MV-025/gate.log`: 8 resource tests passed, 1 Linux-only memory-cap test explicitly skipped on macOS; 362 total passed / 1 skipped. 10,001-file rejection observed in 0.6571 s with 3,613,984 bytes traced Python peak; scanner timeout in 1.0099 s. Sparse sizes, aggregate read cap, random structural bytes, stat/open symlink swap and FD cleanup pass. Coverage measured, not a security guarantee.

### MV-026 — Implement CI and supported-platform verification

- **Priority / status / phase:** P0; **COMPLETE — local and hosted Ubuntu/macOS targets**; `PH-09`. **Requirement(s):** FR-014,FR-016. **Estimated focused effort:** 5–9 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-024,MV-025; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `.github/workflows/ci.yml`, `docs/COMMANDS.md`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Run Linux/macOS lint/format/type/unit/E2E/lock checks on safe fixtures; pin actions; capture failing platforms explicitly. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_e2e.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run ruff check . && uv run mypy src && uv run pytest -q` (then CI matrix); additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** CI green on declared supported platforms or support restricted honestly. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Actual verification:** `verification/MV-026/local-gate.log`: 363 pass / 1 explicit Linux-only skip; lock/lint/format/security/types/build pass on macOS arm64. Workflow YAML parsed locally, action commit/license definitions retained, real ModelScan smoke passes with required Darwin resource insufficiency. User explicitly selected “Finish local candidate; leave hosted CI pending.” CI execution and Linux support remain unverified; this scoped completion permits local PH-10 preparation, not public release.

**Hosted follow-up:** verification/MV-026/hosted-followup/ records the cache failure, clean-cache reproduction, hash-locked setup correction and successful Ubuntu 24.04/macOS 15 Intel matrix at 3d24c0a (run 39465563101). Full checks, fresh installed package and real inert ModelScan pass on both. Local arm64 evidence remains separate; no hosted ARM pass is claimed. CI is now authenticated; independent review/public release and dedicated loader host gates remain pending.

### MV-027 — Produce tutorial examples and reproducibility guide

- **Priority / status / phase:** P0; **COMPLETE**; `PH-10`. **Requirement(s):** FR-013,FR-014. **Estimated focused effort:** 4–7 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-019; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `README.md`, `examples/`, `docs/COMMANDS.md`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Write valid safe example with actual outputs after running; explain scopes, nonclaims, installation/CLI/decision interpretation, and privacy. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_e2e.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_e2e.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** A clean-room developer can follow commands without missing flags or invented results. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Actual verification:** `verification/MV-027/`: five synthetic example variants and inspect run successfully, separate CONTROLS example returns 10, existing fixture paths refuse overwrite. 12 targeted / 364 full-suite pass, one Linux-only skip; lint/types pass. README now describes actual commands, scope, privacy, exits and local-candidate/hosted-pending status.

### MV-028 — Build distribution and public release candidate

- **Priority / status / phase:** P0; **COMPLETE — local candidate scope; public release PENDING**; `PH-10`. **Requirement(s):** FR-014. **Estimated focused effort:** 4–7 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-026,MV-027; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `pyproject.toml`, `uv.lock`, `README.md`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Build wheel/sdist; install fresh env; exercise --help, scan fixture, reports, exit codes and offline behavior; record checksums. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_release.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv build && uv run pytest -q tests/test_release.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** Fresh install and E2E verified; no major security gate outstanding. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Actual verification:** `verification/MV-028/gate.log`: 7 fresh-build/install tests / 371 total pass, one Linux-only skip; lint/format/security/types pass. Built wheel is installed outside the checkout using cached hash-locked runtime dependencies; all four decisions, inspect, unknown-schema failure and runtime network-denial guard pass. Source archive ships specs/examples/CI and excludes operational verification data (initial archive failure retained). Hosted CI/public release remain pending by user-selected scope; no tag or publish.

### MV-029 — Audit licenses, docs, specifications and claims

- **Priority / status / phase:** P0; **COMPLETE — local candidate scope; public release PENDING**; `PH-10`. **Requirement(s):** FR-006,FR-017. **Estimated focused effort:** 2–4 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-028; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `docs/RESEARCH_REFERENCES.md`, `docs/SPEC_AUDIT.md`, `docs/PROGRESS.md`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Run traceability/links/version/cross-doc checks, inspect dependency notices, remove unsupported feature claims; tag only with all gates complete. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/test_release.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/test_release.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** All P0 FRs traceable and verified; release notes honest about unrun P1/P2. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


**Actual verification:** `verification/PH-10/final-gate.log`: 36 targeted / 381 full-suite tests pass, one explicit Linux-only skip; lock/lint/format/security/types/build pass. All 17 P0 requirements map to implemented tests; documentation links/version/claim boundaries and fresh distribution installation pass. License evidence is retained in MV-001/010/024; no dependencies added. Quoted/multiline credential and authorization redaction regressions pass; raw bytes remain private and sensitive. Final local packaging/audit records: `verification/MV-029/` and `verification/PH-10/`. Hosted CI, Linux execution, project review and public release remain pending; no tag or publication.

### MV-030 — Design and independently review isolated loader runner

- **Priority / status / phase:** P2; **NOT STARTED**; `PH-11`. **Requirement(s):** FR-018. **Estimated focused effort:** 15–30 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-023,MV-029; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `src/modelvet/verification/microvm.py`, `tests/isolated/`, `docs/THREAT_MODEL.md`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** On dedicated Linux KVM host harden Firecracker jailer, seccomp/cgroups, no network/secrets/mounts; validate observed containment using controlled fixtures; keep disabled by default. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/isolated/test_microvm.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/isolated/test_microvm.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** Documented approved isolation gate and teardown verified; no host execution. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


### MV-031 — Implement scoped version-specific loader test

- **Priority / status / phase:** P2; **NOT STARTED**; `PH-11`. **Requirement(s):** FR-021. **Estimated focused effort:** 12–25 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-030; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `src/modelvet/verification/loader_context.py`, `tests/isolated/test_version_diff.py`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Pin two approved framework versions and identical fixture digest; run in disposable guest, observe events, separate access/attempt/execute; signpost unexercised paths. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/isolated/test_version_diff.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/isolated/test_version_diff.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** Differences reproducible on harmless controlled fixtures, failure -> INCONCLUSIVE. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.


### MV-032 — Independently adjudicate discrepancy findings

- **Priority / status / phase:** P2; **NOT STARTED**; `PH-11`. **Requirement(s):** FR-018,FR-021. **Estimated focused effort:** 8–15 hours.
- **Purpose/context:** Deliver a bounded, independently testable part of the ModelVet evidence/admission workflow. Preserve the fail-closed invariant in PRD §7 and threat constraints in `THREAT_MODEL.md`.
- **Prerequisites/dependencies:** MV-031; no work should begin before dependent acceptance evidence exists.
- **Expected files:** `benchmarks/loader_cases/`, `docs/BENCHMARK_PLAN.md`. Paths are proposed and may be created only during implementation.
- **Implementation procedure:** Have second method validate observed scanner-loader mismatch; compare applicable existing tools fairly, document novel/missed/unknown cases; do not claim superiority without held-out evidence. In all affected modules add typed errors, traceable status records, and no implicit network or untrusted model execution. Verify tool versions from `TECH_STACK.md` where applicable.
- **Observable behavior:** A successful supported input yields the specific evidence described above; an unsupported/malformed/missing input produces explicit errors or coverage gaps, never implicit `APPROVE`.
- **Tests to add/update:** `tests/isolated/test_version_diff.py`. Include at least one positive, one negative and one incomplete input variation.
- **Planned verification:** `uv run pytest -q tests/isolated/test_version_diff.py`; additionally run `uv run pytest -q` and `uv run ruff check .` after broader suite exists. Commands are unverified until code and environment exist.
- **Acceptance / task DoD:** Every claimed discrepancy has reproducible artifact, scanner, loader and guest identity. Actual command exit/status and test log recorded in `PROGRESS.md`, diff reviewed, security invariants checked, and all relevant source-of-truth docs updated. Do not mark complete on prose alone.

### MV-033 — Verify stored raw evidence

- **Priority / status / phase:** P1; **COMPLETE**; `PH-12`. **Requirement(s):** FR-022.
- **Prerequisites/dependencies:** MV-016; static report contract implemented. No dependency on enabling PH-11.
- **Expected files:** `src/modelvet/reports/audit.py`, `tests/test_report_audit.py`, versioned schema, CLI and REPORT_AUDIT_SPEC.
- **Implementation procedure:** Validate the stored report, securely hash each declared raw attachment, honor aggregate budgets and recheck report identity. Missing, unsafe, mismatched or changing bytes cannot yield VERIFIED. No source artifact is loaded or rescanned.
- **Failure modes:** invalid schema/path, unsafe file, identity drift, exhausted budgets, write/read errors and interruption must remain controlled; no fabricated success.
- **Planned verification:** `uv run pytest -q tests/test_report_audit.py`; then lock/lint/format/security/types/full tests/build.
- **Acceptance / task DoD:** clean, malformed, missing, conflicting, unsupported, budget and failure tests pass; actual logs and security/privacy limits recorded in PROGRESS. No new dependency without review. No admission or authentication claim.

**Actual verification:** verification/MV-033/task.log: 22 targeted pass; gate.log: 508 full-suite pass / one Linux-only skip; lock/lint/format/security/types (52 source files) pass. Secure bounded raw hashing, missing/unsafe/drift/pin/budget paths and 0/30/40 CLI states are verified. This is stored byte consistency, not authentication/admission; no dependency added.

### MV-034 — Compare stored reports

- **Priority / status / phase:** P1; **COMPLETE**; `PH-13`. **Requirement(s):** FR-023.
- **Prerequisites/dependencies:** MV-033; static report contract implemented. No dependency on enabling PH-11.
- **Expected files:** `src/modelvet/reports/compare.py`, `tests/test_report_compare.py`, versioned schema, CLI and REPORT_AUDIT_SPEC.
- **Implementation procedure:** Validate both stored reports; compare artifact/policy/semantic identities and bounded file/check summaries. Hide relative filenames by default, disclose truncation and never recalculate or promote admission.
- **Failure modes:** invalid schema/path, unsafe file, identity drift, exhausted budgets, write/read errors and interruption must remain controlled; no fabricated success.
- **Planned verification:** `uv run pytest -q tests/test_report_compare.py`; then lock/lint/format/security/types/full tests/build.
- **Acceptance / task DoD:** clean, malformed, missing, conflicting, unsupported, budget and failure tests pass; actual logs and security/privacy limits recorded in PROGRESS. No new dependency without review. No admission or authentication claim.

**Actual verification:** verification/MV-034/gate.log: 13 targeted / 521 full-suite pass, one Linux-only skip; lock/lint/format/security/types (53 source files) pass. Run/raw metadata is separate from semantic change; stored policy/decision differences never trigger reevaluation. Relative names/free text are suppressed by default; truncation/counts and drift checks are verified. Initial formatting/type failures retained. Next MV-035.

### MV-035 — Audit an explicit report batch

- **Priority / status / phase:** P1; **COMPLETE**; `PH-14`. **Requirement(s):** FR-024.
- **Prerequisites/dependencies:** MV-033,MV-034; static report contract implemented. No dependency on enabling PH-11.
- **Expected files:** `src/modelvet/reports/batch.py`, `tests/test_report_batch.py`, versioned schema, CLI and REPORT_AUDIT_SPEC.
- **Implementation procedure:** Read a bounded closed local JSON manifest with relative report paths. Enforce one report root and aggregate report/raw budgets; preserve one typed row per input. Any invalid/missing/incomplete row prevents aggregate verification.
- **Failure modes:** invalid schema/path, unsafe file, identity drift, exhausted budgets, write/read errors and interruption must remain controlled; no fabricated success.
- **Planned verification:** `uv run pytest -q tests/test_report_batch.py`; then lock/lint/format/security/types/full tests/build.
- **Acceptance / task DoD:** clean, malformed, missing, conflicting, unsupported, budget and failure tests pass; actual logs and security/privacy limits recorded in PROGRESS. No new dependency without review. No admission or authentication claim.

**Actual verification:** verification/MV-035/gate.log: 29 batch / 558 full-suite tests pass, one Linux-only skip; lock/lint/format/security/types (54 source files) pass. targeted.log: 98 combined phase/CLI/fresh-install cases pass before two final regressions were added; acceptance.log: 33 batch/doc cases pass. examples.log runs the documented clean workflow successfully. Batch limits reserve both report reads, preserve failed rows, reject root/manifest drift and never promote stored admission. Initial test import failure is retained in acceptance-initial.log. Final package identities and release checks are retained alongside these logs; no dependency added.

### MV-036 — Define workbench contracts and lock optional dependencies

- **Priority / status / phase:** P1; **COMPLETE**; `PH-15`. **Requirement(s):** FR-025.
- **Prerequisites:** MV-035 and the user-authorized workbench plan.
- **Procedure / failure modes:** Versioned interface, scope/ADR amendments, exact lockfiles and dependency license/advisory evidence. Smoke-test combined Python dependencies and frontend toolchain. Missing, malformed, conflicting, unsupported and interrupted paths must remain explicit; no model deserialization or policy weakening.
- **Interfaces:** WORKBENCH_SPEC.md.
- **Verification:** `tests/test_workbench_contract.py` plus lock/lint/types/full suite and build as applicable; commands/results recorded in PROGRESS. Planned checks are not verification.
- **DoD:** implemented behavior and actual passing tests, reviewed diff/dependencies, updated source-of-truth documentation; independent release gates remain pending.

**Actual verification:** verification/workbench/MV-036-tests.log: 9 contract/docs tests pass. Combined FastAPI/Pydantic/TestClient/Uvicorn and React/Vite/TypeScript smoke pass; Python and npm lockfiles resolved without peer overrides. TypeScript 7 peer incompatibility was caught and pinned to supported 5.9.3. License metadata/notices and point-in-time OSV/npm audit evidence retained in verification/workbench/.

### MV-037 — Implement authenticated loopback application

- **Priority / status / phase:** P1; **COMPLETE**; `PH-15`. **Requirement(s):** FR-025.
- **Prerequisites:** MV-036.
- **Procedure / failure modes:** Session exchange, exact Host/Origin and CSRF, safe rooted paths, bounded bodies, local assets and capability/policy endpoints. Missing, malformed, conflicting, unsupported and interrupted paths must remain explicit; no model deserialization or policy weakening.
- **Interfaces:** WORKBENCH_SPEC.md.
- **Verification:** `tests/test_workbench_api.py` plus lock/lint/types/full suite and build as applicable; commands/results recorded in PROGRESS. Planned checks are not verification.
- **DoD:** implemented behavior and actual passing tests, reviewed diff/dependencies, updated source-of-truth documentation; independent release gates remain pending.

**Actual verification:** verification/workbench/MV-037-tests.log: 6 authenticated API/security tests pass. Rooted listing, session replay/CSRF/origin/host/body boundaries, policy pins, workspace lock/modes and overlap tests pass; workbench mypy and security lint pass.

### MV-038 — Implement scan workers and private persistent history

- **Priority / status / phase:** P1; **COMPLETE**; `PH-15`. **Requirement(s):** FR-025.
- **Prerequisites:** MV-037.
- **Procedure / failure modes:** Single active worker, fixed own-module argv, observational stages, cancellation/cleanup, restart interruption, private SQLite/report byte pins and workspace lock. Missing, malformed, conflicting, unsupported and interrupted paths must remain explicit; no model deserialization or policy weakening.
- **Interfaces:** WORKBENCH_SPEC.md.
- **Verification:** `tests/test_workbench_jobs.py` plus lock/lint/types/full suite and build as applicable; commands/results recorded in PROGRESS. Planned checks are not verification.
- **DoD:** implemented behavior and actual passing tests, reviewed diff/dependencies, updated source-of-truth documentation; independent release gates remain pending.

**Actual verification:** verification/workbench/MV-038-tests.log: 17 API/worker cases pass; PH-15-gate.log: 599 full-suite pass / one Linux-only skip, lock/lint/format/security/types (64 source files) pass. Real worker scans cover four decisions, CLI semantic parity, callback failure, scanner cancellation/cleanup, index failure and restart/history. Initial security-lint failures are retained separately.

### MV-039 — Build developer shell and scan setup

- **Priority / status / phase:** P1; **COMPLETE**; `PH-16`. **Requirement(s):** FR-026.
- **Prerequisites:** MV-038.
- **Procedure / failure modes:** Responsive dark UI, restricted folder selection, policy setup, capabilities, actual stage/elapsed feedback and controlled errors. Missing, malformed, conflicting, unsupported and interrupted paths must remain explicit; no model deserialization or policy weakening.
- **Interfaces:** WORKBENCH_SPEC.md.
- **Verification:** `frontend/tests/workbench.spec.ts` plus lock/lint/types/full suite and build as applicable; commands/results recorded in PROGRESS. Planned checks are not verification.
- **DoD:** implemented behavior and actual passing tests, reviewed diff/dependencies, updated source-of-truth documentation; independent release gates remain pending.

**Actual verification:** verification/workbench/MV-039-build.log and MV-039-tests.log: TypeScript/production build and 6 component/format/safe-text tests pass. MV-039-browser.log: 2 real Chromium tests pass, covering actual authenticated dashboard/navigation and rooted folder → worker scan → report → history.

### MV-040 — Build visual evidence workspace

- **Priority / status / phase:** P1; **NOT STARTED**; `PH-16`. **Requirement(s):** FR-026.
- **Prerequisites:** MV-039.
- **Procedure / failure modes:** Decision/explanation, searchable file/check coverage, evidence details, findings/claims/conflicts, safe text, paging and accessible controls. Missing, malformed, conflicting, unsupported and interrupted paths must remain explicit; no model deserialization or policy weakening.
- **Interfaces:** WORKBENCH_SPEC.md.
- **Verification:** `frontend/tests/workbench.spec.ts` plus lock/lint/types/full suite and build as applicable; commands/results recorded in PROGRESS. Planned checks are not verification.
- **DoD:** implemented behavior and actual passing tests, reviewed diff/dependencies, updated source-of-truth documentation; independent release gates remain pending.

### MV-041 — Add history, import, comparison and guidance

- **Priority / status / phase:** P1; **NOT STARTED**; `PH-16`. **Requirement(s):** FR-026.
- **Prerequisites:** MV-040.
- **Procedure / failure modes:** Persistent run navigation, exact-byte import/download, raw verification, existing comparison service, deterministic check/rule guidance, demo separation. Missing, malformed, conflicting, unsupported and interrupted paths must remain explicit; no model deserialization or policy weakening.
- **Interfaces:** WORKBENCH_SPEC.md.
- **Verification:** `tests/test_workbench_reports.py` plus lock/lint/types/full suite and build as applicable; commands/results recorded in PROGRESS. Planned checks are not verification.
- **DoD:** implemented behavior and actual passing tests, reviewed diff/dependencies, updated source-of-truth documentation; independent release gates remain pending.

### MV-042 — Complete workbench fault and browser acceptance

- **Priority / status / phase:** P1; **NOT STARTED**; `PH-17`. **Requirement(s):** FR-027.
- **Prerequisites:** MV-041.
- **Procedure / failure modes:** CLI/UI semantic parity, all decisions, browser auth/path/XSS boundaries, interruption/disk/read errors, no false approval, responsive/keyboard/reduced-motion. Missing, malformed, conflicting, unsupported and interrupted paths must remain explicit; no model deserialization or policy weakening.
- **Interfaces:** WORKBENCH_SPEC.md.
- **Verification:** `tests/test_workbench_security.py` plus lock/lint/types/full suite and build as applicable; commands/results recorded in PROGRESS. Planned checks are not verification.
- **DoD:** implemented behavior and actual passing tests, reviewed diff/dependencies, updated source-of-truth documentation; independent release gates remain pending.

### MV-043 — Package assets and extend supported CI

- **Priority / status / phase:** P1; **NOT STARTED**; `PH-17`. **Requirement(s):** FR-027.
- **Prerequisites:** MV-042.
- **Procedure / failure modes:** Frontend assets in wheel/sdist, no Node needed at runtime, optional-extra isolation, generated-type drift check, pinned Ubuntu/macOS frontend/browser gate. Missing, malformed, conflicting, unsupported and interrupted paths must remain explicit; no model deserialization or policy weakening.
- **Interfaces:** WORKBENCH_SPEC.md.
- **Verification:** `tests/test_workbench_release.py` plus lock/lint/types/full suite and build as applicable; commands/results recorded in PROGRESS. Planned checks are not verification.
- **DoD:** implemented behavior and actual passing tests, reviewed diff/dependencies, updated source-of-truth documentation; independent release gates remain pending.

### MV-044 — Document and hand off local preview

- **Priority / status / phase:** P1; **NOT STARTED**; `PH-17`. **Requirement(s):** FR-027.
- **Prerequisites:** MV-043.
- **Procedure / failure modes:** Offline demonstration reports, launch/privacy/scanner/recovery tutorial, actual gate logs/hashes and clear external release/research/loader gates. Missing, malformed, conflicting, unsupported and interrupted paths must remain explicit; no model deserialization or policy weakening.
- **Interfaces:** WORKBENCH_SPEC.md.
- **Verification:** `tests/test_workbench_contract.py` plus lock/lint/types/full suite and build as applicable; commands/results recorded in PROGRESS. Planned checks are not verification.
- **DoD:** implemented behavior and actual passing tests, reviewed diff/dependencies, updated source-of-truth documentation; independent release gates remain pending.

## Next task

MV-036 starts the authorized PH-15–17 workbench extension. Proceed one coherent task at a time through MV-044; optional loader/research gates remain pending.
