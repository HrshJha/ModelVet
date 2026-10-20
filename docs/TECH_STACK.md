# Technology stack and compatibility decisions

**Status: static candidate implemented; Ubuntu/macOS Intel hosted gates passed**, 2026-10-20. `pyproject.toml` and `uv.lock` resolve 30 third-party packages. Python 3.12.15, uv 0.13.3, Typer 0.27.3, Pydantic 2.14.1, Hatchling 1.32.4, pytest 9.1.1, pytest-cov 7.1.0, Hypothesis 6.170.5, Ruff 0.17.1, mypy 2.4.0 and packaging 26.3 are pinned. macOS packaging evidence and license/advisory review are in `verification/MV-001/`; ModelScan 0.8.8 compatibility is observed on macOS in a separate environment; Ubuntu 24.04/macOS 15 Intel hosted validation now passes; actual results are tracked in verification/MV-026/hosted-followup/. The register below retains the original proposal as historical context; the actual manifest and lock control installed versions.

## Concrete baseline

- **Python:** CPython `3.12.x` (planned `requires-python = '>=3.12,<3.13'` for MVP). Chosen conservatively because upstream ModelScan README documents Python 3.9–3.12 support; revisit once newer support is tested. Python is not the future isolated loader runtime; P2 may test other interpreters inside microVMs.
- **Environment/lock:** `uv` `0.13.0` candidate as of 2026-10-09; commit `uv.lock`. Use `uv python pin 3.12`, `uv sync --locked` after scaffolding.
- **Build backend:** `hatchling`, PyPI distribution metadata and exact version to be frozen by MV-001 (not checked for combined compatibility here).
- **CLI:** `typer==0.27.3` (published 2026-10-06); Rich is a transitive dependency, but color must be optional; don't add `rich` direct until justified.
- **Typed data:** `pydantic==2.14.1` (published 2026-10-11), for schema validation, deterministic JSON compatibility and enums.
- **Config:** builtin `tomllib` read-only; use TOML (no PyYAML dependency). TOML writing is unnecessary for MVP.
- **Hash/inventory/temp/ZIP:** stdlib `hashlib`, `pathlib`, `os`, `stat`, `tempfile`, `zipfile`, `struct`, `json`, `importlib.metadata`; **never invoke pickle deserialization**.
- **Structural safetensors:** stdlib bound/validate header per official specification; no full tensor loading, no `torch` required for MVP.
- **Scanner:** external `modelscan` executable as **optional installation but required where policy applies**; version pinned after adapter's exact fixture smoke tests; don't import modelscan into core process.
- **Tests:** pytest and pytest-cov; Hypothesis `6.170.5` (published 2026-10-20) for parser/property tests; exact pytest/pytest-cov versions to lock/verify in MV-001.
- **Quality:** Ruff, mypy, packaging/build, optional `pip-audit` or OSV-Scanner; exact versions to resolve and verify in MV-001.
- **CI:** GitHub Actions for lint/types/schema, unit and safe fixture E2E; no real model downloads, no model loading, and pin third-party actions to immutable commit SHAs when workflow is added.
- **Later P2 isolation:** Linux KVM + Firecracker, jailer, seccomp, cgroups and independent host, **not an MVP dependency**.

## Dependency register

| Package/tool | Proposed version/range | Role / module | Type | Publication/compatibility caveat | License/source |
|---|---|---|---|---|---|
| CPython | `3.12.x` | all | toolchain | ModelScan upstream documents <=3.12; OS installation needs verification | https://www.python.org/downloads/ |
| uv | `0.13.0` | install/lock/build | toolchain | Published 2026-10-09; command behavior must be tested locally | https://github.com/astral-sh/uv/releases |
| typer | `==0.27.3` | `cli` | runtime | PyPI release verified; combo not locked | https://pypi.org/project/typer/ |
| pydantic | `==2.14.1` | `evidence`, `policies` | runtime | PyPI release verified; combo not locked | https://pypi.org/project/pydantic/ |
| hatchling | **pin in MV-001** | packaging | build | exact version not independently verified | https://pypi.org/project/hatchling/ |
| modelscan | **pin in MV-010** | scanner subprocess | optional runtime | supported Python 3.9–3.12 per README; CLI 0–4; version-specific reporting must be tested | https://github.com/protectai/modelscan |
| pytest | **pin in MV-001** | tests | development | no combination test yet | https://docs.pytest.org/ |
| pytest-cov | **pin in MV-001** | coverage | development | no combination test yet | https://pytest-cov.readthedocs.io/ |
| hypothesis | `==6.170.5` | property tests | development | PyPI release verified; Python 3.12 wheel shown | https://pypi.org/project/hypothesis/ |
| ruff | **pin in MV-001** | lint/format | development | exact version unverified | https://docs.astral.sh/ruff/ |
| mypy | **pin in MV-001** | type checking | development | exact version unverified | https://mypy.readthedocs.io/ |
| build | **pin in MV-001 if needed** | dist validation | development | uv build may avoid separate package | https://packaging.python.org/ |
| pip-audit | **pin in MV-024 if selected** | dependency audit | development | optional; check supported CLI/OSV alternative | https://github.com/pypa/pip-audit |

**Distribution licenses:** check each installed package's metadata, NOTICE/attribution and transitive restrictions at lock time (MV-001/MV-024). Package project page is evidence of existence, not proof that all transitive licenses are acceptable. Source publication != cross-dependency compatibility.

## Expected `pyproject.toml` design (illustrative; create in MV-001)

```toml
[project]
name = "modelvet"
version = "0.1.0"
description = "Evidence-backed local ML model admission verification"
requires-python = ">=3.12,<3.13"
dependencies = ["typer==0.27.3", "pydantic==2.14.1"]

[project.scripts]
modelvet = "modelvet.cli.main:app"

[build-system]
requires = ["hatchling"] # PIN WHEN RESOLVING
build-backend = "hatchling.build"

[dependency-groups]
dev = ["pytest", "pytest-cov", "hypothesis==6.170.5", "ruff", "mypy"] # LOCK IN MV-001
```

## Installation / update policy

- `uv python install 3.12` (conditional on tool available); `uv python pin 3.12` (planned); `uv lock`; `uv sync --locked`; `uv run modelvet --help` (only after code exists).
- Before committing `uv.lock`, verify `uv pip list`, installed versions, license inventory and `modelscan --version` if adapter enabled. CI must use `uv sync --locked`.
- ModelScan is an **external executable**: `uv tool install modelscan==<verified-version>` or isolated tool env after MV-010; cannot use an unverified literal exact version in current docs.
- `uv lock --upgrade-package NAME` only through reviewed dependency task, with full gate.

## Rejected or deferred technologies

No FastAPI/HTTP endpoints, Docker/Kubernetes hosting, Postgres, Redis, Celery, ML model inference stack, LangChain, LLM judgement, cloud credentials, PyYAML, or full PyTorch dependency in MVP. No forced scanners besides a pinned optional/mandated-by-policy ModelScan adapter. Firecracker isolated loader testing is P2 and Linux-only; building a host-side mock sandbox would be misleading.

## Compatibility verification plan

MV-001: create manifest, `uv lock`, install on supported Python, run Typer/Pydantic import smoke tests, complete license inventory. MV-010: pin ModelScan and test JSON content and exit mappings against frozen synthetic cases. MV-026: repeat CI on Linux and macOS; do not claim Windows until independently tested. Open question OQ-01 documents any outstanding version decisions.

## MV-010 external environment checkpoint

ModelScan 0.8.8 is pinned separately in `tools/modelscan/requirements.lock` with eight packages and hashes. Core runtime dependencies remain unchanged. Exact upstream metadata, installed wheel notices (including NumPy bundled GPL/GCC-exception and LGPL notices) and OSV query evidence are in `verification/MV-010/`. This repository does not redistribute scanner binaries/environment; any redistribution requires retaining applicable notices and a fresh license review. Real inert-fixture smoke passed on macOS; memory caps and archive scope remain limited as documented.
