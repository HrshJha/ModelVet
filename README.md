# ModelVet

Local static assessment of model artifacts, with independent coverage, deterministic admission rules and private JSON/Markdown reports.

**Status:** local v0.1.0 candidate; public release pending. macOS arm64/Python 3.12.15 has local evidence. Hosted Ubuntu 24.04 and macOS 15 Intel pass the full static gate. Windows is unsupported. No independently reviewed benchmark or model-loading experiment has been performed. A local synthetic development pilot is explicitly INCONCLUSIVE.

## Local browser workbench

Scan a local folder, inspect decisions and coverage, review evidence, revisit history and compare runs without writing commands. The dark workbench uses the same static engine as the CLI.

```sh
uv sync --locked --extra ui
uv run --extra ui modelvet ui --models-root /absolute/path/to/models
```

Compiled assets ship with the Python package; Node is a development dependency only. The service binds to `127.0.0.1` and uses a private authenticated session. Keep the workspace outside the model root. See the [launch, privacy, recovery and demonstration guide](docs/WORKBENCH_GUIDE.md). Workbench preview verification is recorded separately from the earlier hosted static gate.

## What it does

- Creates bounded private snapshots, rejects unsafe filesystem entries and computes exact file/manifest SHA-256 identities.
- Inspects a conservative subset of safetensors headers and ZIP indexes as bytes, without extraction or model deserialization.
- Records sourced local license/provenance and explicit dependency declarations, preserving missing information and conflicts.
- Uses a separately installed, pinned ModelScan executable when applicable; retains bounded original and normalized evidence.
- Reconciles each applicable file/check pair and evaluates independent BLOCK, INSUFFICIENT, named CONTROLS, then APPROVE.
- Writes schema-validated reports outside input using private, atomic, non-overwriting output.
- Verifies declared raw report attachments, compares stored report semantics, and audits explicit report batches with shared limits.
- Optionally matches declared exact PyPI versions against an explicitly supplied offline OSV snapshot, as supplementary evidence.

`APPROVE` means configured static predicates completed on the exact artifact under the recorded policy. It does not establish malware freedom, loader safety, legal rights or verified provenance. ModelVet does not load models, import repository code, download artifacts or use an LLM judge.

## Run locally

Prerequisites: [uv 0.13.3](https://github.com/astral-sh/uv/releases/tag/0.13.3), Python 3.12 (checked: 3.12.15), POSIX Linux/macOS. Ubuntu 24.04 has hosted validation; macOS arm64 has local validation. macOS 15 Intel also has hosted validation.

```sh
uv sync --locked
uv run modelvet version --json
uv run modelvet doctor --json
uv run modelvet policy validate examples/default.toml --json
uv run modelvet scan /absolute/path/to/model --out /separate/private/reports --json-summary
```

The last command requires your actual directory. Follow [safe synthetic examples](examples/README.md) for a workflow needing no model or scanner installation. Build a wheel/sdist with `uv build`; no verified public PyPI release is claimed.

```text
modelvet scan ARTIFACT_DIR [--policy FILE] [--out DIR] [--scanner auto|modelscan|none]
              [--timeout-sec N] [--max-files N] [--max-file-mib N] [--max-total-mib N]
              [--format json|markdown|both] [--quiet] [--json-summary]
modelvet inspect REPORT.json [--format text|json] [--show-evidence]
modelvet advisories REPORT.json --as-of UTC_RFC3339 [--snapshot FILE]
                    [--max-age-days N] [--required|--optional]
modelvet verify REPORT.json [--expected-report-sha256 HEX]
modelvet compare BEFORE.json AFTER.json [--show-paths] [--fail-on-change]
modelvet audit-batch MANIFEST.json --root REPORT_ROOT
modelvet policy validate POLICY.toml [--json]
modelvet doctor [--json]
modelvet version [--json]
modelvet ui --models-root DIR [--workspace DIR] [--port 0] [--no-browser]
```

| Exit | Meaning |
|---:|---|
| 0 | Scoped APPROVE or successful non-scan command |
| 10 | CONTROLS; named conditions and owners apply |
| 20 | BLOCK; independently supported explicit prohibition |
| 30 | INSUFFICIENT, incomplete audit/supplement, or requested semantic-change signal |
| 40 | Invalid input/config/schema/budgets/paths |
| 50 | Failure before a defensible report could be completed |
| 130 | Interrupted |

JSON machine output uses stdout; routine scan status/errors use stderr. Summary `report` paths are relative to the selected output root; absolute host roots are redacted. JSON is always saved, including with `--format markdown`. `doctor` exit 0 means diagnostics completed: inspect availability/readiness fields. `inspect` validates a stored assertion; a digest is not a signature or independent attestation.

The optional `advisories` command emits JSON evidence bound to an existing report and a local snapshot; it does not recompute admission. Required unresolved evidence or any affected-version match returns 30. Optional unresolved evidence may return 0 while remaining visibly unknown; 0 is not an admission verdict. It makes no network calls. See [format, scope and examples](docs/ADVISORY_SPEC.md).

The [stored-report audit commands](docs/REPORT_AUDIT_SPEC.md) emit JSON without changing their inputs. `verify` and `audit-batch` return 0 only when declared byte checks complete; incomplete evidence returns 30. `compare` returns 0 on a completed comparison, or 30 on semantic change with `--fail-on-change`. These results do not recompute admission or authenticate authors. Paths are suppressed by default; use `umask 077` for redirected output.

## Policy, scanner and limits

The [default policy](examples/default.toml) requires every applicable check and sourced LICENSE/PROVENANCE declarations. Independently confirmed repository Python is prohibited. Unknown formats, mismatches, unresolved findings and declared remote/custom loader behavior remain insufficient. [Policy v1](docs/POLICY_SPEC.md) defines exact fields/rules/controls. [Example controls](examples/controls.toml) demonstrate conditional admission; replace the example owner and enforce deployment conditions yourself.

Keep ModelScan in its [separate hash-locked environment](tools/modelscan/README.md). `--scanner none` yields INSUFFICIENT when an applicable mandatory scanner check is missing. The supported safetensors-only example needs no scanner.

Hard ceilings: 10,000 entries including directories, 1 GiB/file, 2 GiB total, 16 MiB/metadata read, depth 64, scanner 120 seconds. Flags may lower these limits. Policies are limited to 64 KiB; reports to 32 MiB. Oversized inputs are rejected without implicit approval.

Current limitations:

- ZIP64, streaming descriptors, encryption and other ZIP subsets are unsupported; archive/member scanner completeness remains unproven.
- The tested macOS host cannot enforce scanner OS memory bounds. Required resource evidence stays UNSUPPORTED even when named file proof completes. Linux caps and the real inert scanner contract pass on hosted Ubuntu 24.04; this does not establish containment for arbitrary scanner code.
- An external scanner is not a sandbox; OS network isolation is not enforced.
- Metadata/dependency fields are declarations, not legal clearance, verified lineage, actual installed versions or vulnerability clearance. Optional [offline advisory enrichment](docs/ADVISORY_SPEC.md) is supplementary; ranges and unsupported semantics remain unresolved.
- Final source/snapshot rechecks are best-effort mutation detection, not an atomic filesystem transaction.
- Free text redacts host paths/common credential patterns. Exact artifact filenames, operator policy/owners and original raw evidence can remain sensitive; keep reports private.

## Verification and release state

```sh
uv lock --check
uv run ruff check .
uv run ruff format --check .
uv run ruff check src --select S
uv run mypy src
uv run pytest -q
uv build
```

Actual commands/results, including initial failures, are in [PROGRESS](docs/PROGRESS.md) and `docs/verification/`. The [hosted Ubuntu/macOS matrix passes](https://github.com/HrshJha/ModelVet/actions/runs/39465563101); public release remains pending independent project/security review. PH-08 offline advisory enrichment is implemented separately; independent benchmark acceptance and gated PH-11 loading remain pending. A ten-case development corpus and local pilot are documented in [benchmarks](benchmarks/README.md); no superiority claim is supported by synthetic tests. The [PH-11 review packet](docs/LOADER_REVIEW_PACKET.md) records pending prerequisites and enables no execution.

Start with [PRD](PRD.md), [architecture](docs/ARCHITECTURE.md), [threat model](docs/THREAT_MODEL.md), [security handling](docs/SECURITY_POLICY.md) and [ADRs](docs/DECISIONS.md). ADRs remain Proposed until explicit project review. MIT licensed; dependency metadata/notices are retained in verification evidence. The external scanner is not redistributed in the core wheel.
