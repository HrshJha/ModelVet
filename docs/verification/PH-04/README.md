# PH-04 checkpoint — 2026-10-20

MV-010–013 complete on macOS arm64/Python 3.12.15/uv 0.13.3, uncommitted against base `e2f2bb2`. `final-gate.log` records lock validation, lint, formatting, mypy, 201 tests and isolated wheel/sdist build, all exit 0. Earlier failed type and nested-NaN checks remain preserved. Core/scanner dependency consistency checks and real inert scan/normalization smokes are in MV-010/011.

After the documentation update, `package-final.log` records a fresh build; `artifacts.json` records wheel/sdist hashes. `whitespace-and-package.log` confirms all three schemas are packaged and 51 new source/test/schema/config files pass whitespace inspection. A trailing blank in pyproject was fixed; the initial check is retained separately.

Implemented: external ModelScan 0.8.8 environment/adapter; strict v1 evidence schema; separate process/check/result/finding verification; independently materialized applicability v2; per-file terminal coverage; preserved claim, identity and assessment conflicts. Missing, duplicate, skipped, unsupported, malformed or mismatched mandatory evidence cannot become completed coverage. Scanner findings remain REPORTED. No admission engine exists yet, so no ModelVet APPROVE/BLOCK decision is claimed.

ModelScan's named standalone pickle-file proof is observed. Archive member completeness is INCONCLUSIVE. Darwin memory APIs reject tested limits, so resource proof remains UNSUPPORTED; CPU/file/FD/output/wall limits are enforced. No OS network isolation or scanner sandbox is claimed. Exact external dependencies, notices and advisory snapshot are retained separately; no scanner package is imported into core.

Source files, schemas, tests and progress are saved uncommitted. Next phase: PH-05 (MV-014 evaluator, MV-015 policy TOML), followed by reporting/reproducibility and end-to-end CLI integration. Linux/security/release gates, optional benchmarks and gated loader research remain pending.
