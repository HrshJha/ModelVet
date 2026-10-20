# Static report auditing — PH-12–14

These commands operate on stored report assertions. No model loading, artifact rescan, policy evaluation, network request or author authentication occurs. The old report v1 schema/policy remains unchanged.

## PH-12 / MV-033 — verify

`modelvet verify REPORT.json [--expected-report-sha256 HEX]`

Validate report JSON and declared raw attachment identities. Read only `raw/<declared-sha256>.bin` under the report's own directory, using descriptor-based no-follow access. Reject links/special files and hash bounded bytes with before/after identity checks. Default hard limits: 64 attachments, 32 MiB total raw bytes (each existing report attachment is already capped at 4 MiB). Recheck the report's exact bytes after attachment reads. An optional external byte SHA-256 pin binds the entire stored report, including observational fields.

Output is typed JSON with report/artifact/semantic identity, declared/verified/unresolved counts and per-attachment states. VERIFIED requires every declared attachment and report identity check to pass. Missing, unsafe, unreadable, size/hash mismatch, drift or budgets yield INCOMPLETE. Output is bounded and signals omitted attachment rows. Exit 0 is successful local verification, 30 incomplete evidence, 40 invalid arguments/report, 50 orchestration failure, 130 interruption. It is not an APPROVE verdict. Extra undeclared files are not inspected. Filesystem checks are best effort, not an atomic snapshot.

## PH-13 / MV-034 — compare

`modelvet compare BEFORE.json AFTER.json [--show-paths] [--fail-on-change]`

Validate both reports and compare semantic digests, artifact/policy identities, stored decisions, file changes and normalized check changes. Observation-only run/raw changes do not become semantic changes. Show exact counts and at most 200 changed file/check rows, explicitly reporting omitted rows. Relative names are hashed by default; --show-paths is explicit disclosure. No free-text metadata or raw bytes are echoed. Exit 0 means comparison completed; --fail-on-change selects 30 on semantic change. Neither exit is an admission decision.

## PH-14 / MV-035 — audit-batch

`modelvet audit-batch MANIFEST.json --root REPORT_ROOT`

A closed local JSON manifest is version 1.0.0 with `reports` rows containing canonical relative `path` and optional `expected_report_sha256`. No absolute/traversal paths, aliases, symlinks, recursive discovery or executable references. Maximum 32 unique reports, manifest 64 KiB, aggregate charged report JSON 128 MiB and aggregate raw reads 128 MiB. Each captured report is charged twice its byte length to reserve the initial read and bounded final identity recheck. The charge is conservative even if validation fails before the recheck. Each report must also fit the 32 MiB report and 32 MiB raw-evidence ceilings; declared raw size must fit the remaining budget before hashing. Budgets can only decrease internally. Failures are recorded per row and do not erase later rows. Exhaustion preserves explicitly unprocessed rows. No invalid/incomplete/unprocessed row can yield aggregate VERIFIED. Output suppresses paths and preserves input order/index/hash IDs. No report is changed. Exit 0 requires all rows verified, otherwise 30; an invalid manifest/root is 40.

Each phase starts only after its prerequisite task verification. Source/report changes during reads, malformed records, wrong external pins, count/byte limits, missing files and partial failures require tests. No dependency addition is planned. Implementation status and actual evidence are maintained in TASKS/PROGRESS.

## Schemas, privacy and evidence

The packaged v1 schemas are `report-audit-v1.json`, `report-comparison-v1.json`, `report-batch-manifest-v1.json` and `report-batch-audit-v1.json`. All result records contain `admission_recomputed: false`; a VERIFIED byte audit may accompany any stored admission decision, including INSUFFICIENT or BLOCK. It does not promote that decision. An unpinned self-consistent report may have an untrusted author; an external report hash is meaningful only when supplied through a trusted channel.

Results go to stdout. Use `umask 077` before redirecting them to files; the commands do not create report files or enforce shell redirection permissions. Digests and optional relative names remain sensitive or linkable. Batch output always suppresses input paths; comparison discloses relative names only with `--show-paths`.

Actual phase gates are recorded in `verification/MV-033/` through `verification/MV-035/`. No dependencies or model execution were added.
