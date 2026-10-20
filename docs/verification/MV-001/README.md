# MV-001 packaging evidence — 2026-10-20

Scope: package foundation only, on macOS arm64/Python 3.12.15/uv 0.13.3. Base commit `e2f2bb269683d79cd6a12757aa140357fef089ad`; implementation is uncommitted. No scanner is installed or imported by ModelVet, no artifact scanning or model execution has been implemented, and no Linux or release acceptance is claimed.

## Commands and evidence

- Required chain: `uv lock --check && uv sync --locked && uv run python -c "import typer, pydantic" && uv build` — exit 0, `task-verification.log`.
- `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`, `uv pip check` — logs named `tests`, `lint`, `format`, `types`, `dependency-check`.
- `package-compatibility.log`: a fresh temporary Python 3.12 environment installs the wheel without dependencies and imports the package with Typer, Pydantic, ModelScan and torch absent. This only tests lightweight package import, not a functioning CLI.
- `environment.json` records interpreter, OS and base commit. Build products are ignored under `dist/`.

Initial failed checks are retained with `-initial` suffix. They exposed a lock needing regeneration after build constraints, metadata field ordering in a test, a long test line, and Ruff formatting Markdown by default. All were corrected. An exploratory `uv pip install --no-deps --python-version 3.13 --dry-run` did not enforce the Python restriction; no installer-enforcement claim is made. The supported range is tested directly through package metadata.

## Dependency rationale and review

Only Typer (CLI) and Pydantic (future typed evidence) are direct runtime dependencies. Hatchling builds the package; pytest/pytest-cov/Hypothesis support the documented test gates; Ruff/mypy provide code checks; packaging validates Python support metadata. Hatchling is also locked in the development group, with its build dependencies constrained for isolated builds. ModelScan remains an external future adapter dependency.

All 30 locked third-party versions use the PyPI registry, with distribution hashes in `uv.lock`. Exact-version publisher metadata and yanked-file/advisory responses are in `dependency-metadata.json`. No yanked file or advisory match was returned at review time. `osv-query.json` and `osv-response.json` preserve the independent advisory lookup. These queries cannot establish that packages are vulnerability-free; supply-chain compromise and undisclosed defects remain possible. Dependencies were installed from wheels; ModelVet's own build uses the pinned Hatchling backend.

Wheel LICENSE/NOTICE texts and hashes are preserved for every locked dependency, including platform-conditional colorama. Runtime dependency notices include MIT, BSD, ISC and Python/PSF terms; development dependencies additionally include Apache-2.0 and MPL-2.0 (Hypothesis/pathspec), with bundled component notices retained. Development tools are not bundled into the ModelVet wheel. Keep applicable upstream notices on redistribution and re-audit changes; this is an engineering inventory, not legal clearance. CPython uses the PSF license; uv is MIT/Apache-2.0 dual-licensed.

Security review: the package root contains only a docstring and version; there are no artifact parsers, scanner launches, dynamic imports, network clients or model loader calls. Missing scanner functionality cannot generate a successful assessment. No operational secrets or hostile fixtures were added.
