# MV-034 / PH-13 — stored report comparison

2026-10-20, macOS arm64/Python 3.12.15/uv 0.13.3. Initial source formatting/type errors and a test import ordering failure are retained. task.log initially 12 pass; gate.log: 13 targeted / 521 full-suite pass, one Linux-only skip; lock/lint/format/security/types (53 source files) pass.

Executed: `uv lock --check && uv run ruff check . && uv run ruff format --check . && uv run ruff check src --select S && uv run mypy src && uv run pytest -q tests/test_report_compare.py && uv run pytest -q`.

Compare validates/rechecks both stored reports; separates semantic and observational identity; counts file/check changes with bounded rows. Paths are suppressed by default and unrecognized check IDs are hashed; free text is not echoed. Exact relative paths require --show-paths and remain sensitive/linkable. No admission evaluation, raw attachment read, model loading or author authentication. No dependency addition.
