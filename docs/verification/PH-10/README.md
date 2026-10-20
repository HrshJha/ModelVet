# PH-10 local candidate completion — 2026-10-20

Local scope complete; hosted CI/public release pending by user selection. Platform: macOS arm64, Python 3.12.15, uv 0.13.3. Base commit e2f2bb269683d79cd6a12757aa140357fef089ad, saved uncommitted. No tag, push or publication.

## Final full gate

Executed command (results in final-gate.log):

```sh
uv lock --check &&
uv run pytest -q tests/test_release.py tests/test_docs_contract.py tests/test_reports.py &&
uv run ruff check . &&
uv run ruff format --check . &&
uv run ruff check src --select S &&
uv run mypy src &&
uv run pytest -q &&
uv build
```

Exit 0: 36 targeted pass, 381 full-suite pass / one Linux-only OS memory-limit skip, 74 Python files formatted, 46 source files type checked, both distributions built. Initial S105 regex-name false positive is retained in final-gate-initial.log; successful rerun above follows the variable rename.

Only status documentation changed after that gate. completion-checks.log records exit 0 with 10 passing release/doc-contract cases and both archives rebuilt, from:

```sh
uv run pytest -q tests/test_release.py tests/test_docs_contract.py &&
uv lock --check &&
uv build
```
 Release tests themselves build/install in a fresh environment outside the checkout from cached hash-locked runtime dependencies and run actual CLI cases with socket connection attempts denied. This does not establish OS network containment for an external scanner.

whitespace-review.json records no-index diff checks of source/tests/specs/config/examples/workflow and the uncommitted checkpoint. artifacts.json records SHA-256/size for both final distributions and the dependency lock, plus archive-content observations. Operational verification records are intentionally excluded from the sdist; the checkout retains them.

## Limits and next gates

Hosted Ubuntu/macOS workflow has not run (GitHub CLI not signed in); Linux resource-limit execution remains unverified. Real ModelScan 0.8.8 standalone proof was checked on macOS, but required memory-resource coverage remains UNSUPPORTED/INSUFFICIENT there. Archive-member completeness remains inconclusive. A subprocess is not a sandbox. Redaction is best effort and private raw bytes may contain sensitive data. No benchmark or model execution was run. ADRs remain Proposed; project review and public release gates remain in ../../RELEASE_STATUS.md.

## Subsequent MV-020 work

The original PH-10 distributions matching artifacts.json are now preserved in ignored `dist/checkpoints/PH-10/`. Root dist files are rebuilt for subsequent optional advisory work; current hashes/results are in ../MV-020/. PH-10 gate records remain historical.
