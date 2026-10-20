# MV-022 local development corpus

2026-10-20, macOS arm64, Python 3.12.15/uv 0.13.3; uncommitted base e2f2bb269683d79cd6a12757aa140357fef089ad. No dependency addition. `uv run pytest -q tests/test_benchmark_manifest.py`: 28 pass (task.log). `uv run ruff check . && uv run mypy src && uv run pytest -q`: exit 0, 462 pass / one Linux-only skip (gate.log). Initial type-check output is retained separately.

Engineering implemented: ten deterministic inert recipes; exact file/artifact identity; closed manifest schema; alternative stdlib byte-method labels; private non-overwriting materialization; link/budget/malformed/tamper checks. Corpus and manifest creation command are in ../../../benchmarks/README.md. Generator changes invalidate the frozen hash.

Independent review and hidden holdout remain PENDING. These same-author development method checks are not independent human adjudication, malware ground truth, loader evidence or superiority research. MV-023 can run an explicitly labeled development pilot; PH-08 research acceptance is not passed by these unit tests.
