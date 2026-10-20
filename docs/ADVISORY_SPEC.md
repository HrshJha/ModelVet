# Offline advisory evidence — MV-020 / FR-019

The optional `advisories` command assesses declared dependency pins from a schema-validated stored report against an explicitly supplied local snapshot. It emits a supplementary JSON document and never mutates that report or recalculates admission. If advisory evidence is required by an operational workflow, require successful exits from both `scan` and `advisories`. Policy v1 has no advisory predicates; no hidden advisory check is added to the static MVP policy.

```text
modelvet advisories REPORT.json --as-of UTC_RFC3339
                    [--snapshot FILE] [--max-age-days 7] [--required|--optional]
```

Required is the default. Exit 30 means a reported affected-version match, or unresolved required advisory evidence. Exit 0 means the supplementary check completed under the selected requirement level; it is not an APPROVE verdict. Optional mode can exit 0 with UNKNOWN/NOT_RUN, which remain visible. Matches always return 30, including optional mode. Invalid input/schema/unsafe path is 40; orchestration failure 50; interruption 130. JSON alone goes to stdout. No network request, package install, source import or model loading occurs.

## Snapshot envelope

See [synthetic snapshot](../examples/advisory-snapshot.json) and [declared environment](../examples/advisory-environment.json). Envelope fields are closed:

- `schema_version`: `1.0.0` (ModelVet envelope version, distinct from embedded OSV version).
- `generated_at`: UTC RFC3339; `source`: operator-supplied source description, not authenticated. Output retains a SHA-256 of the source claim to avoid echoing paths/credentials.
- `queries`: at most 1,000 exact `(ecosystem, normalized package name, version string)` entries. Duplicate identities are rejected.
- Each query has `package: {name, ecosystem}`, `version`, explicit boolean `complete`, and `response`.
- `response` has `vulns` (full OSV records, empty/default list permitted) and optional `next_page_token`. A nonempty token or `complete=false` is partial. Copy all pages before claiming completeness; query provenance is an operator assertion.

A raw OSV record, raw API batch response or unscoped vulnerability list is not this envelope. Omitted queries cannot establish negative evidence. Requiring an explicit query identity avoids treating an empty/incomplete feed as a universal no-match. This does not authenticate the publisher or detect an operator's false completeness declaration.

Reads are capped at 16 MiB, 100,000 structural tokens/depth 64, 1,000 total advisory records, 1,000 affected entries/record and 10,000 versions/entry. Symlinks (including ancestors), hardlinks, special nodes, duplicate JSON keys, nonfinite numbers and read-time identity changes are rejected. Both `modified` and `withdrawn`, when present, must be UTC and no later than snapshot generation. Unknown envelope/query fields are invalid; extra OSV fields are ignored as allowed for compatible schema evolution.

## Matching and freshness

- Only declared exact PyPI pins are eligible. PyPI names normalize runs of `.`, `_`, `-` to `-` and lowercase. Version strings compare exactly; aliases such as `1.0` and `1.0.0` are not silently equated.
- OSV schema major 1 is recognized. An explicit version in a matching affected-package entry records `AFFECTED_VERSION`, with advisory ID and snapshot SHA-256/JSON pointer. It is a supplied-record assertion, not proof that software is installed or an operation exploitable.
- Ranges (including ECOSYSTEM/SEMVER/GIT), ecosystem-specific conditions, unknown schema major, missing affected versions or mismatched package evidence remain unresolved. A known exact match is retained alongside unresolved range semantics.
- Withdrawn records do not produce active matches. No-match evidence is `NO_MATCH_IN_SNAPSHOT`, limited to the supplied exact complete query and supported record subset.
- Future-dated or older-than-maximum-age snapshots are INCONCLUSIVE. Maximum age is 0–365 days, default 7; the boundary is inclusive. `--as-of` is explicit and bound into the output so reproduction does not depend on the current clock. Stale positive records remain visible, with inconclusive freshness.
- Missing snapshot is NOT_RUN. Missing query, ambiguous/duplicate dependency pins and an empty dependency set cannot complete a required assessment. Unsupported ecosystems or unpinned declarations remain unsupported.

## Output and identity

[advisories-v1.json](../schemas/advisories-v1.json) describes the supplementary document: `assessment`, `semantic_digest`, `exit_code`. Assessment includes the source report's semantic digest, artifact digest, snapshot digest, generation/evaluation time, age threshold/requirement level, per-dependency statuses/results/references and limitations. The semantic digest uses domain `modelvet-advisories-v1` plus NUL and canonical sorted JSON. It binds all these inputs, including the explicit evaluation time; it is not an author signature.

The original snapshot stays at the operator's selected location; preserve it privately beside the emitted JSON for later reference verification. ModelVet does not copy the feed into an existing scan report. Exact dependency identities and original snapshot content may be sensitive. Keep redirected output private (for example `umask 077`) and outside scanned artifact directories. No aggregate vulnerability score, legal conclusion, global clearance or admission promotion is produced.
