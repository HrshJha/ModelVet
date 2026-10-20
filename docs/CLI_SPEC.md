# CLI interface contract — local static candidate

**Program:** `modelvet`; Python console script set in `pyproject.toml`. Local and noninteractive by default. Commands and flags here supersede illustrative snippets elsewhere. MV-002 implements the grammar/help/version and explicit unavailable errors; MV-015 implements bounded `policy validate` with success 0/invalid input 40. Full CLI/report integration is now locally tested; hosted CI remains pending. See `COMMANDS.md` for operational status.

## Implemented hierarchy

```text
modelvet --help
modelvet version [--json]
modelvet doctor [--json]
modelvet policy validate POLICY.toml [--json]
modelvet scan ARTIFACT_DIR [--policy POLICY.toml] [--out OUT_DIR]
                 [--scanner auto|modelscan|none] [--timeout-sec 120]
                 [--max-files 10000] [--max-file-mib 1024] [--max-total-mib 2048]
                 [--format json|markdown|both] [--quiet] [--json-summary]
modelvet inspect REPORT.json [--format text|json] [--show-evidence]
modelvet advisories REPORT.json --as-of UTC_RFC3339 [--snapshot FILE]
                    [--max-age-days N] [--required|--optional]
```

- `scan` requires an existing directory. `--policy` default is installed conservative `default-policy-v1` embedded package resource, validated. `--out` defaults to an external state directory under `~/.local/state/modelvet/reports/` (resolved for the host; must never be inside scanned input); explicit `--out` must be outside input and snapshot root.
- `--scanner auto` runs ModelScan if available; if required but unavailable, create `NOT_RUN` required check and `INSUFFICIENT`, **not** an approval. `none` is permitted for diagnostic/evidence-only runs and triggers insufficiency when applicable scanner mandatory. Tool version must match pinned allowlist.
- `--timeout-sec` applies scanner wall clock and hard cap; no execution mode option in MVP.
- `--json-summary` emits a single bounded JSON object on stdout (decision, report paths, rule IDs); `--quiet` hides routine status on stderr but never errors. Never leak host paths in summary when redaction enabled.
- `--format` controls file outputs, not whether a security decision is generated. JSON is always internally required; `--format markdown` still writes JSON beside MD for audit, unless revised via ADR. The simplest default is `both`.
- `inspect` **does not** recalculate policy from untrusted output; verifies JSON schema and prints stored decision and evidence. Must not interpret report strings as executable Markdown/HTML.
- `policy validate` accepts TOML file; checks unknown keys, missing check/format mappings, contradictory rule definitions, unknown control IDs and size limits.
- `doctor` probes Python, platform, ModelScan binary/version, temporary/output folder permissions; may not scan unknown model contents or call the network.
- `version` reports installed ModelVet version/schema support; not a proof of app security.

## Exit status mapping

| Code | Meaning | CI behavior |
|---:|---|---|
| 0 | Scan `APPROVE` or non-scan command success | success |
| 10 | `CONTROLS` conditional admission | nonzero; caller explicitly handles |
| 20 | `BLOCK` | nonzero; reject |
| 30 | `INSUFFICIENT` | nonzero; do not infer clean |
| 40 | Invalid input/config/schema/output path | usage/data error |
| 50 | Internal orchestration failure where no defensible report exists | fail CI |
| 130 | User interrupt (SIGINT) | interrupted |

Partial scanner failure with report is `INSUFFICIENT/30`, not internal error `50`; if report building itself fails, `50`. Individual scanner exit codes are **not** forwarded directly.

## Output and interactivity

- Normal human summary on stderr (even on exit 20/30): decision, unresolved required checks, artifact short digest, report paths. Structured JSON only on stdout when `--json-summary` to protect automation.
- `NO_COLOR=1` disables styling, `CI=1` disables animations, no TTY prompts. Path escaping suitable for whitespace/Unicode filenames; shell-quote user-provided paths.
- No automatic overwrite of an existing report run directory. Proposed layout: `$OUT/<12-char-artifact-digest>/<run-id>/report.json`, `report.md`, optional restricted `raw/`. `run-id` is random opaque ID; semantic digest is deterministic and separate.
- All output written atomically, with owner-only modes where OS supports them. Never write inside ARTIFACT_DIR. Write required checks/results before human summary to avoid misleading terminal success.
- Missing optional scanner output may be retained with `UNKNOWN` but not counted complete.

## Command forms (executed synthetic examples: verification/MV-027)

```sh
modelvet scan './fixtures/benign' --policy ./examples/default.toml --out ./out --json-summary
modelvet inspect './out/example/report.json' --show-evidence
modelvet policy validate ./examples/default.toml
modelvet doctor --json
modelvet version
```

Illustrative JSON summary when required scanner proof is unavailable (actual identities vary):

```json
{"decision":"INSUFFICIENT","exit_code":30,"rule_ids":["MISSING-MANDATORY"],"report":"<path-not-real>"}
```

## Failure cases and user journeys

| Objective / initial state | Command | Response and evidence | Failure / acceptance |
|---|---|---|---|
| Audit new local model | `scan dir --out out` | local snapshot/identity, scanner and coverage evidence, reports | no silent missing-check pass |
| Recheck prior report | `inspect report.json` | stored decision and evidence references | malformed schema exit 40; no model load |
| Check local environment | `doctor` | status for tool paths and permissions | unavailable optional tool is visible |
| Review TOML | `policy validate file.toml` | validated rule names and applicability | contradictory rule fails before scan |
| CI gate | `scan dir --json-summary` | machine summary on stdout, detailed diagnostics stderr | 10/20/30 distinguish conditions |
| Mutation or timeout | `scan` on changing fixture | FAILED identity / scanner with reasons | exit 30/40, never 0 |

## Configuration precedence

`CLI flags > explicitly selected TOML file > embedded default-policy-v1 and conservative default limits`. Environment variables must not alter security policy implicitly. `NO_COLOR`/`CI` affect presentation only. Enforce global hard ceilings even if user requests larger resources until explicitly reviewed. No accidental network by default.

## Implemented privacy/inspection behavior

Summary report paths are relative to the selected output root; report_root is <redacted>. Doctor exit 0 means diagnostics completed, not readiness. Inspect validates a stored assertion without authenticating its author. Human Markdown is escaped; terminal free text strips controls and evidence uses JSON escaping. All five commands are exercised locally and in a fresh installed wheel. External scanner/platform limitations remain explicit.

## MV-020 supplementary advisory command

`advisories` is an optional P1 command described in [ADVISORY_SPEC](ADVISORY_SPEC.md). It reads declared pins from a validated stored report and an explicit local snapshot, emits a schema-validated JSON supplement, and preserves the stored report. It never recomputes admission. Required stale/absent/partial/unsupported evidence is unresolved/30; any affected-version match is 30. Optional unknown evidence may exit 0 with visible statuses. This success code is not APPROVE. UTC `--as-of` is mandatory for reproducibility; no runtime network access is implemented.

## Optional synthetic development pilot

`uv run python -m modelvet.benchmarks.runner --manifest benchmarks/manifest.json --out out/NEW_DIRECTORY [--repeats 2] [--timeout-sec 120]` runs only the validated closed inert recipes. The root must be new; output is private. Return 30 for the explicit INCONCLUSIVE research result; 40 invalid arguments/input, 50 failure before result publication, 130 interruption. The completed result marker is written last; failed runs may retain private partial evidence. Exact local execution/limitations are in BENCHMARK_PLAN and benchmarks/README.md. It is separate from admission and is not an independently adjudicated efficacy benchmark.

## Implemented stored-report audits — PH-12–14

`verify REPORT.json [--expected-report-sha256 HEX]`, `compare BEFORE.json AFTER.json [--show-paths] [--fail-on-change]`, and `audit-batch MANIFEST.json --root REPORT_ROOT` emit typed JSON to stdout. Verify/batch use 0 for VERIFIED and 30 for incomplete checks; compare uses 0 for a completed comparison or 30 for semantic differences when requested. Common errors remain 40/50/130. These are stored assertion/byte workflows, not admission decisions. No network or model access occurs. See [REPORT_AUDIT_SPEC](REPORT_AUDIT_SPEC.md) for bounds, schemas, privacy and partial failures.
