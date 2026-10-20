# MV-020 — offline advisory supplement, 2026-10-20

Base e2f2bb269683d79cd6a12757aa140357fef089ad; source remains uncommitted. macOS arm64, Python 3.12.15, uv 0.13.3. No additional third-party dependency or lock change.

## Executed checks

- task-initial.log: first 39 advisory cases passed.
- task.log: expanded 46 cases passed.
- targeted-final.log: `uv run pytest -q tests/test_advisories.py tests/test_cli.py tests/test_release.py`, exit 0, 77 pass.
- gate.log: command below, exit 0; 50 targeted and 434 full-suite pass, one Linux-only OS memory cap skip; 76 Python files formatted, 47 source files type checked.
- gate-initial.log: earlier full gate, exit 0, 428 pass / one skip before additional output-integrity cases.
- initial-lint.log and initial-types.log retain intermediate formatting and Literal annotation errors, corrected before successful gate.

```sh
uv lock --check &&
uv run pytest -q tests/test_advisories.py &&
uv run ruff check . &&
uv run ruff format --check . &&
uv run ruff check src --select S &&
uv run mypy src &&
uv run pytest -q
```

completion.log records final documentation/release contract checks and wheel/sdist build after status updates. artifacts.json records current archive/lock hashes and contents; original PH-10 archives are preserved in ignored dist/checkpoints/PH-10/. whitespace-review.json records the no-index diff audit for untracked implementation/spec files.

## Implemented boundary

Explicit local, query-scoped OSV envelope, no runtime network. Exact PyPI enumerated-version matching only; unsupported ranges/conditions/ecosystems are unresolved. Required missing/stale/future/partial data cannot complete the supplementary gate. Affected-version assertions retain advisory ID, snapshot SHA-256 and JSON pointer; these do not prove actual installation or exploitability. Duplicate/conflicting identities and malformed/linked/special/oversized/changing inputs fail safely.

The supplementary document binds the original report/artifact and explicit evaluation time. JSON schema, aggregate status, result, source-reference binding, digest and exit classification are validated. Tests verify source reports remain byte-identical, and the installed CLI works with socket connections denied. Exact source/completeness remains an unauthenticated operator claim. No broad feed completeness, admission recalculation, benchmark, loader capability, hosted CI pass or public release is claimed. See ../../ADVISORY_SPEC.md. Next MV-022 corpus/ground-truth work.
