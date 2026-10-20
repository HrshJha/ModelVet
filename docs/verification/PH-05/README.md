# PH-05 checkpoint — 2026-10-20

MV-014–015 complete on macOS arm64/Python 3.12.15/uv 0.13.3. Saved work is uncommitted against base e2f2bb2; original user documentation remains present. No dependencies were added, and ADRs remain Proposed.

## Executed checks

`final-gate.log` records this exact exit-0 chain:

```sh
uv lock --check && uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run pytest -q && uv build
```

287 tests passed; 53 Python files satisfy formatting; 38 source files pass strict mypy. The 29 policy cases include 1,296 exhaustive status combinations under each of two policies. The 58 config cases include bounded/deep/malformed TOML, unknown and contradictory rules, unsafe files, drift, semantic hashes, schema snapshots and CLI success/error handling. Earlier type/lint and parent-symlink failures are explained in the MV-014/015 evidence; the actual failed type/parser logs are retained.

`package-smoke.log` records byte comparison of the default policy and all five schemas in the wheel, default inclusion in sdist, then a disposable fresh environment with hash-verified locked runtime requirements, dependency-free wheel installation and isolated default/schema resource loading. `package-final.log` and `artifacts.json` identify the final documentation-inclusive wheel/sdist build. `whitespace-review.log` records whitespace review of 86 source/test/schema/config/doc files and a prohibited-call scan. The initial review found one extra blank line at the end of .gitignore; it was removed, and `whitespace-review-initial.log` retains the failure.

## Scope and limits

The evaluator binds core facts to the manifest, reconstructs applicability/coverage and applies independent BLOCK, INSUFFICIENT, CONTROLS, APPROVE precedence. Empty/model-free inventories, unknown formats, missing mandatory proof, tampered coverage, relevant conflicts and unresolved findings cannot approve. Controls include IDs/owners; deployment enforcement is external. Repository Python presence is the only independently supported ban category; scanner labels do not prove malicious operations. Policy validation works, with bounded local reads and controlled failures.

Full scan/report orchestration remains pending. Existing archive/member proof and Darwin memory-limit gaps remain unresolved. Linux/security/CI/release acceptance, optional benchmarks and gated loader research have not run. Next: PH-06 starting MV-016 reports, followed by repeatability and supporting CLI commands.
