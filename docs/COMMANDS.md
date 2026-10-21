# Operational command reference — PLANNED / CONDITIONAL / VERIFIED

**As of 2026-10-20: foundation/static/evidence checks verified through PH-05; full scan/report commands remain PLANNED**. The package scaffold, lock and smoke tests exist. The CLI shell and policy validation exist; artifact-assessment orchestration is pending. All commands below are **PLANNED** instructions for future implementations, or **CONDITIONAL** for optional environments. Do not paste a fabricated green test result into PROGRESS. Commands assume the future repository root, POSIX shell and UV installed; check actual CLI versions before use.

| Status | Exact command | Purpose / preconditions |
|---|---|---|
| PLANNED | `uv python install 3.12` | Python setup; requires uv and internet/available distro |
| PLANNED | `uv python pin 3.12` | Pin interpreter; creates `.python-version` |
| PLANNED | `uv lock` | Resolve project lock after creating pyproject |
| PLANNED | `uv sync --locked` | Install exact pinned project+dev deps |
| PLANNED | `uv lock --check` | Verify lockfile agrees with manifest |
| PLANNED | `uv run python -c 'import typer, pydantic; print("deps imported")'` | Import smoke |
| PLANNED | `uv run pytest -q tests/test_identity.py` | Focused identity tests (after task MV-005) |
| PLANNED | `uv run pytest -q tests/test_coverage.py tests/test_policy.py` | Core evidence/policy tests |
| PLANNED | `uv run pytest -q tests/test_e2e.py` | Full local safe-fixture scenario |
| PLANNED | `uv run pytest -q` | Full normal safe suite |
| PLANNED | `uv run pytest --cov=modelvet --cov-report=term-missing` | Coverage reporting, after pytest-cov installed |
| PLANNED | `uv run ruff check .` | Lint |
| PLANNED | `uv run ruff format --check .` | Format check |
| PLANNED | `uv run ruff format .` | Format write (review diff) |
| PLANNED | `uv run mypy src` | Static typing |
| CONDITIONAL | `uv run pip-audit` | If approved and installed; review package CLI and lock mode before use |
| PLANNED | `uv build` | Build sdist/wheel after hatchling pinned |
| PLANNED | `uv pip install --python .venv/bin/python dist/modelvet-*.whl` | Local install (requires wheel and POSIX venv); glob must match single file |
| PLANNED | `uv run modelvet --help` | CLI help once implemented |
| PLANNED | `uv run modelvet doctor --json` | Tool/env check, no model load |
| PLANNED | `uv run modelvet policy validate examples/default.toml` | Validate policy after example exists |
| PLANNED | `uv run modelvet scan tests/fixtures/e2e/complete_safe_fixture --policy examples/default.toml --out ./out --json-summary` | Safe local E2E; ensure `out` isn't inside input |
| PLANNED | `uv run modelvet inspect ./out/REPLACE_WITH_REAL_REPORT.json` | Illustrative placeholder must be replaced with actual output path |
| PLANNED | `uv run pytest -q tests/test_evidence.py tests/test_reports.py` | Schema/documentation-model check |
| PLANNED | `uv run python -m modelvet.benchmarks.runner --manifest benchmarks/manifest.json --out benchmarks/results/` | Benchmark script after MV-022 and MV-023 exist; proposed args |
| CONDITIONAL | `uv run pytest -q tests/isolated` | Only on approved Linux/KVM lab, P2 VM security gate passed |
| PLANNED | `uv lock --check && uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run pytest -q && uv build` | CI-equivalent local verification after scaffold |

## Version and exit-code cross-check

- When using a real pinned ModelScan binary, upstream shows `modelscan -p /path/to/model --reporting-format json --output-file /tmp/modelscan.json`; **CONDITIONAL**, because installation, version-specific schema and invocation are not verified here. Its upstream exit statuses are 0=no issue, 1=findings, 2=error, 3=no supported files, 4=usage. ModelVet own decision exits are **0/10/20/30**, errors **40/50**, interruption **130**.
- `pip-audit` exact invocation and its lockfile handling require verification during MV-024; never claim it ran from this document.
- Reports go outside inspected input and new run directories are not overwritten.

## Documentation/spec audit (currently executable independently of app)

- Inspect Markdown: `find . -type f -name '*.md' | sort`.
- Validate references/IDs using the **blueprint-specific audit script executed during documentation creation**, not a future ModelVet CLI. Its output is summarized in `SPEC_AUDIT.md`; no application tests are implied.
- When actual source exists, add a repository script/test for schema/traceability docs (`tests/test_docs_contract.py`) or keep the audit script in CI; record accurate command in this file.

## Failure interpretation

If any planned command fails before project is initialized, **that's expected**, not a verified feature failure. If `uv sync` cannot resolve dependencies, update `TECH_STACK` and ADR with exact conflict rather than upgrading silently. If tests cannot reproduce expected status, task remains incomplete and blocked; preserve logs.

## Verified foundation checkpoint — MV-001 (2026-10-20)

`uv lock --check`, `uv sync --locked`, Typer/Pydantic import smoke, `uv build`, `uv run pytest -q` (3 passed), Ruff lint/format, `uv run mypy src` and `uv pip check` succeeded on macOS arm64/Python 3.12.15/uv 0.13.3. A fresh wheel imports with no runtime dependencies installed. See `verification/MV-001/README.md` for logs, initial failures and limitations. The table above remains the planned command catalog; only the specifically recorded foundation checks are verified.

PH-02 verification: `uv run pytest -q tests/test_input_gate.py`, `tests/test_snapshot.py`, `tests/test_identity.py` and `tests/test_classify.py` each passed at their task checkpoint; full suite 81 passed, lint/format/types/lock/build exit 0. Logs: `verification/MV-003/` through `verification/MV-006/`. `uv run modelvet --help`/version work; scan remains unavailable after input validation.

PH-03 final verification: `uv lock --check && uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run pytest -q && uv build` — exit 0 on macOS, 140 tests passed; `verification/PH-03/final-gate.log`. This verifies implemented foundation/static modules only; scan/report commands remain incomplete.

PH-04 final gate: `uv lock --check && uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run pytest -q && uv build` — exit 0, 201 tests, macOS (`verification/PH-04/final-gate.log`). Separate scanner lock install/version, 17 adapter contracts and real inert scan/normalization smokes are recorded under MV-010/011. Core/scanner `uv pip check` pass. CLI scan/inspect/doctor/policy validate remain placeholders except path validation; no admission/report workflow is verified.

PH-05 final gate: `uv lock --check && uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run pytest -q && uv build` — exit 0, 287 tests, 38 source files type-checked. Exact task commands `uv run pytest -q tests/test_policy.py` (27 initially; 29 in final suite) and `uv run pytest -q tests/test_policy_config.py` (58) pass. `uv run modelvet policy validate src/modelvet/policies/default.toml --json` returns 0 and the effective policy digest. Fresh runtime dependencies were exported with `uv export --locked --no-dev --no-emit-project --format requirements-txt`, installed with hash verification in a disposable environment, and the built wheel loaded its default and schema resources using isolated Python. Logs: `verification/PH-05/`, `verification/MV-014/`, `verification/MV-015/`. No complete scan/report command is verified yet.

PH-06/07 implemented commands: scan, inspect, policy validate, doctor and version now work. PH-09 local gate is recorded in verification/MV-026/local-gate.log (363 passed / one Linux-only skip). `uv run ruff check src --select S` also passes after the reviewed S603 suppression at the single controlled subprocess boundary. `.github/workflows/ci.yml` targets ubuntu-24.04/macOS-15 with immutable action commits; Ruby Psych parsed it locally. No hosted CI has run. Local-candidate scope was explicitly selected by the user; Linux remains experimental/unverified. Public release waits for hosted CI and project security review.

MV-020 optional command: `uv run modelvet advisories REPORT.json --snapshot FILE --as-of 2026-10-20T12:00:00Z`. Required unresolved evidence or affected-version matches exit 30; optional unknown evidence may exit 0 with its status unchanged. It never recomputes admission. `uv run pytest -q tests/test_advisories.py` passes 50 cases; full gate 434 pass / one Linux-only skip, lint/format/security/types pass (verification/MV-020/gate.log). Snapshot/example/output contract: ADVISORY_SPEC.md.

MV-022/023 executed local development pilot: `PATH="$PWD/.scanner-venv/bin:$PATH" uv run python -m modelvet.benchmarks.runner --manifest benchmarks/manifest.json --out out/development-pilot-20261020 --repeats 2`, expected/actual exit 30, INCONCLUSIVE, 40 observations. This is a development experiment, not admission or an independent efficacy benchmark. Tests: `uv run pytest -q tests/test_benchmark_manifest.py tests/test_benchmark_metrics.py tests/test_release.py` gives 60 pass. Full lock/lint/format/security/types/test gate: 486 pass / one Linux-only skip. Final installed-package/build checks and all actual outputs: verification/MV-023/.

PH-12–14 executed gate: `uv lock --check && uv run ruff check . && uv run ruff format --check . && uv run ruff check src --select S && uv run mypy src && uv run pytest -q tests/test_report_batch.py && uv run pytest -q` — exit 0; 29 targeted / 558 full-suite pass, one Linux-only skip; mypy checks 54 source files. Prior phase commands: 22 verify tests / 13 compare tests. Combined installed-package/CLI/phase selection passed 98 cases before final regressions; batch/doc acceptance passed 33. The first and final shell blocks in examples/README.md ran together under `set -eu`/`umask 077`, producing VERIFIED byte/batch audits and same_semantics=true. See verification/MV-033–035 for initial failures, reruns, final build and post-doc release checks.

MV-026 hosted follow-up: `gh auth login --hostname github.com --git-protocol https --web` completed after explicit user authorization. Failed hosted jobs exposed a cold uv index-cache prerequisite; CI now primes exported hash-locked runtime dependencies before offline release tests. A fresh-cache reproduction passes 12 release/CI contracts after the fix. [Hosted run 39465563101](https://github.com/HrshJha/ModelVet/actions/runs/39465563101) passes Ubuntu 24.04/macOS 15 Intel, including full tests/build/fresh installation and real inert scanner contracts. No independent review or dedicated loader host is implied. Exact output: verification/MV-026/hosted-followup/.

## Workbench preview commands

From the repository root: `uv sync --locked --extra ui`, then `uv run --extra ui modelvet ui --models-root /absolute/path/to/models`. Node is not needed at runtime. See [WORKBENCH_GUIDE](WORKBENCH_GUIDE.md) for frontend development, one-use session privacy, separate pinned scanner setup and the complete synthetic correction/comparison workflow. Actual local/hosted results live in PROGRESS; installing or listing commands does not verify a gate.
