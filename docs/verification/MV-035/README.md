# MV-035 / PH-14 — explicit stored-report batch audit

2026-10-20, macOS arm64/Python 3.12.15/uv 0.13.3. The user selected “Extend the local feature plan”; PH-12–14 are implemented. No dependency or admission policy changes; PH-11 and external gates remain pending.

## Executed validation

- task-initial.log: 63 combined audit/compare/batch tests pass before final regression additions.
- targeted.log: 98 combined phase/CLI/fresh-install tests pass before final regression additions.
- acceptance-initial.log: incorrect test-only import failed; corrected in acceptance.log (33 batch/doc tests pass).
- gate.log (same bytes as gate-initial.log): `uv lock --check && uv run ruff check . && uv run ruff format --check . && uv run ruff check src --select S && uv run mypy src && uv run pytest -q tests/test_report_batch.py && uv run pytest -q` exits 0. 29 batch / 558 full-suite pass; one explicit Linux-only skip; types cover 54 source files.
- examples.log: exact first and final shell blocks from examples/README.md execute with set -eu and umask 077; verify/batch VERIFIED, comparison semantically equal; all commands exit 0.

post-doc-targeted.log: 103 phase/CLI/documentation/fresh-installed-package tests pass. final-build.log: isolated sdist and wheel build succeeds. Archive/source hashes and whitespace review are retained here. Prior root distributions were preserved under ignored dist/checkpoints/pre-report-audit/ before rebuilding. No commit, push, tag or publication was performed by the agent.

## Limits and security

The manifest is closed, bounded to 32 unique relative paths/64 KiB and rooted explicitly. Report JSON charge reserves twice each captured byte count, covering the initial read and bounded recheck; aggregate ceiling 128 MiB. Declared raw bytes must fit remaining limits before hashing; actual raw reads are counted, with 128 MiB aggregate and 32 MiB per-report ceilings. Each row survives failures; invalid/incomplete/unprocessed/drifting inputs cannot yield aggregate VERIFIED. Filename aliases, links and special files are rejected.

This is local stored byte consistency. All result records fix admission_recomputed=false; tests prove byte verification leaves INSUFFICIENT admission intact. Inputs are unchanged; original model directories are unnecessary. Paths/free text are suppressed by default and no network is used; hashes can remain linkable. Filesystem identity rechecks are best effort, not atomic snapshots or author signatures. Stdout redirection permissions belong to callers. No model or repository code is executed.

## Final package audit

`uv run python docs/verification/MV-035/verify_candidate.py` passes: all packaged Python/policy bytes and all 13 schemas match source; source archive matches 137 source/test/spec/example/config files and excludes operational evidence. `artifacts.json` records archive SHA-256/sizes, source hashes, observed HEAD/worktree and unchanged uv.lock. `git diff --check` passes; no-index whitespace checks cover new files too. The initial audit utility incorrectly treated git's content-difference exit 1 as whitespace failure; whitespace-initial.json retains that attempt, and whitespace-review.json records zero actual problems. The standalone ledger's initial datetime alias lint failure and correction are retained; final-static.log passes lint/format/security/types and uv pip check (30 installed third-party packages).

No installed-source product change followed the full test run. The final documentation contract passes four tests, and final-build.log records the resulting distributions. Local hosted CI/Linux/independent-review/publication limitations remain as documented; PH-11 remains disabled.
