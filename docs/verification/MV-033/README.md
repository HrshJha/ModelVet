# MV-033 / PH-12 — stored raw evidence verification

2026-10-20, macOS arm64, Python 3.12.15/uv 0.13.3. `uv run pytest -q tests/test_report_audit.py`: 22 pass (task.log). `uv lock --check && uv run ruff check . && uv run ruff format --check . && uv run ruff check src --select S && uv run mypy src && uv run pytest -q`: exit 0; 508 pass / one Linux-only skip, 52 source files checked (gate.log).

Declared raw files are opened relative to secure directory descriptors; links/special files are refused; bounded streaming SHA-256, size/identity/pin checks and budgets are explicit. Report bytes are rechecked after hashing. Bad/missing/omitted bytes cannot yield VERIFIED. No report/model is changed, no model is loaded, no admission is recomputed and no author is authenticated. No dependency addition. See ../../REPORT_AUDIT_SPEC.md.
