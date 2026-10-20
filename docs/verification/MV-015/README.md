# MV-015 verification — 2026-10-20

`uv run pytest -q tests/test_policy_config.py`: 58 passed (`task-final.log`). Initial run: 57 passed / 1 parent-symlink exception failure (`task.log`); fixed by translating directory-open OSError to controlled InvalidInput. Final lint/types pass (`lint.log`, `types.log`). No dependency or lock additions.

`uv run modelvet policy validate src/modelvet/policies/default.toml --json`: exit 0 (`cli-smoke.log`), policy digest `sha256:d7de8bfeccfb859c8e0f790fc44602e36102b3a20f2351ea397428ced0900ab6`. CLI tests also verify malformed/missing policy exit 40 with no policy contents or host paths printed. Bounded TOML, duplicate/unknown/contradictory rules, unsafe files, drift, schema snapshots, control owners and semantic identity pass. Embedded default and schemas load from a fresh wheel install (`../PH-05/package-smoke.log`). Remaining scan/inspect/doctor commands are still unavailable.
