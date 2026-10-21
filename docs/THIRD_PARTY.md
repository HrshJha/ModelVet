# Third-party dependency review — local candidate

ModelVet source is MIT licensed. Core distributions contain ModelVet code and its LICENSE; dependencies are separately installed, not vendored. Development dependencies are not required by the installed CLI. This records publisher metadata/retained notices, not legal clearance for model artifacts.

## Core and development lock

All 30 third-party package/version pins match the foundation snapshot. Classifier/text entries fill incomplete metadata from retained notices. Runtime/development split and hashes: pyproject.toml/uv.lock.

| Package | Version | Observed license |
|---|---|---|
| annotated-doc | 0.0.5 | MIT |
| annotated-types | 0.8.0 | MIT |
| ast-serialize | 0.13.1 | MIT |
| colorama | 0.4.6 | BSD-3-Clause (retained text) |
| coverage | 7.16.2 | Apache-2.0 |
| hatchling | 1.32.4 | MIT |
| hypothesis | 6.170.5 | MPL-2.0 |
| iniconfig | 2.3.1 | MIT |
| librt | 0.16.0 | MIT |
| markdown-it-py | 4.2.0 | MIT (classifier/text) |
| mdurl | 0.1.2 | MIT (classifier/text) |
| mypy | 2.4.0 | MIT |
| mypy-extensions | 1.1.0 | MIT |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pathspec | 1.1.1 | MPL-2.0 (classifier/text) |
| pluggy | 1.7.0 | MIT |
| pydantic | 2.14.1 | MIT |
| pydantic-core | 2.50.1 | MIT |
| pygments | 2.21.0 | BSD-2-Clause |
| pytest | 9.1.1 | MIT |
| pytest-cov | 7.1.0 | MIT |
| rich | 15.0.0 | MIT |
| ruff | 0.17.1 | MIT |
| shellingham | 1.5.4 | ISC License |
| sortedcontainers | 2.4.0 | Apache 2.0 |
| tomlkit | 0.15.2 | MIT |
| trove-classifiers | 2026.9.21.13 | Apache-2.0 (classifier/text) |
| typer | 0.27.3 | MIT |
| typing-extensions | 4.16.0 | PSF-2.0 |
| typing-inspection | 0.4.4 | MIT |

## Separate scanner environment

ModelScan 0.8.8 is Apache-2.0; the separate eight-package lock is tools/modelscan/requirements.lock. It is not bundled in the core candidate. Original notices/source URLs are retained in verification/MV-010/scanner-license-files.json and scanner-license-texts.txt. NumPy main metadata lists BSD-3-Clause, 0BSD, MIT, Zlib and CC0-1.0; bundled components additionally carry LGPL/GPL-with-runtime-exception notices. Preserve distribution notices if redistributing that scanner environment; core does not redistribute these binaries. TensorFlow/h5py extras were not installed.

## Evidence and limits

Original core LICENSE/NOTICE files are retained in verification/MV-001/license-files.json and third-party-license-texts.txt, including a hash-verified conditional colorama wheel. A fresh OSV query covered 35 unique locked core/scanner package-version pairs with zero advisory matches on 2026-10-20 (verification/MV-024/dependency-audit.json). This is point-in-time known-advisory matching, not absence-of-vulnerabilities evidence. Development queries sent package names/versions only, never model bytes or credentials.

Generated fixtures are local synthetic bytes under the repository MIT license. No trained weights, executable malicious payload, PKWARE specification or third-party scanner source is redistributed in examples. Official CI action commit/license metadata is retained separately. Hosted CI and explicit project review remain public-release gates. Operational verification records are excluded from the source archive; they remain in the local checkout.

## Optional workbench distribution

FastAPI 0.156.0 and Uvicorn 0.54.0 are an optional `ui` extra; the locked Python graph and license texts are retained in `verification/workbench/`. The combined Python 3.12/Pydantic stack is exercised by API, worker and fresh installed-wheel tests. Core CLI installations retain their original dependencies.

Bundled runtime code uses React/React DOM/scheduler (MIT), Lucide (ISC), and Vite's client helper (MIT); full upstream notices ship in `modelvet/workbench/static/THIRD_PARTY_NOTICES.txt`. Frontend source, package lock and notice generator ship in the source distribution. Node modules and browser session state are excluded. Build/test tools are not installed as Python runtime dependencies. The unmodified axe and Rolldown packages use MPL-2.0; they remain development tools, with no source modifications redistributed here. Other locked development licenses are MIT, Apache-2.0, ISC, BSD-3-Clause, Python-2.0 and MIT-or-CC0. Lock metadata records every package's declared license; this inventory is not a legal determination.

The refreshed npm audit on 2026-10-21 returned zero known matches across the 108-package graph, including platform-specific optional packages. Package names/versions and public registry metadata only were used. This is point-in-time advisory matching, not proof of security. `actions/setup-node` is pinned to the official v6 commit `249970729cb0ef3589644e2896645e5dc5ba9c38`; it receives no persisted repository credentials and package-manager caching is disabled. No scanner binary, trained weight or browser executable is redistributed in the Python package.
