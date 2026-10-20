# MV-026 hosted CI follow-up — 2026-10-20

GitHub CLI sign-in succeeded as HrshJha after explicit user authorization; no credentials are retained here. The repository is private. Previously inaccessible hosted CI is now observed: run 39456019043 failed on Ubuntu/macOS because fresh offline release installation could not resolve annotated-doc from the unprimed uv index cache. This corrects earlier unverified statements that hosted CI had never run.

The workflow now primes only hash-locked runtime dependencies in a separate temporary environment while setup networking is allowed. Release tests retain offline installation and socket-denied runtime checks. No dependency or security limit changes. A regression checks that priming precedes offline tests. A completely new cache/virtual environment reproduced the offline cache failure, then passed 12 release/CI-contract tests after priming (cold-cache.log); two CI contracts pass (task.log). Raw logs are retained privately in out/hosted-ci-followup; displayed logs redact temporary paths or select failure lines.

Hosted rerun results must be inspected before marking MV-026 complete beyond local scope. PH-08 independent review/hidden holdout, public release/risk acceptance and PH-11 dedicated Linux/KVM/isolation review remain outstanding. A GitHub-hosted static Linux runner does not satisfy the dedicated loader laboratory requirement.

Local follow-up gate passes 559 tests / one Linux-only skip, lock/lint/format/security/types (54 source files). Exact combined output: local-gate.log. No dependency changes; hosted results still require inspection.

Ubuntu job 118773868942 at candidate feb9e8d passes all steps: 560 full-suite tests, 10 release tests, and real inert ModelScan with COMPLETE scanner resources/scoped APPROVE. Its original log SHA and selected lines are in ubuntu-summary.json; job/step metadata is in hosted-results.json. macos-15 ARM remains queued; the workflow selects the documented standard macos-15-intel runner for the same full macOS gate, while local arm64 evidence remains separately labeled. This is an OS/architecture target choice, not a claim that queued work passed.
