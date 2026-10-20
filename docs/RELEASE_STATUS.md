# Local v0.1.0 candidate and release gates

The user selected **“Finish local candidate; leave hosted CI pending.”** PH-06/07 and the local portions of PH-09/10 are implemented. This is not a public release, hosted CI pass or independent security certification. Work remains uncommitted in the shared checkout; base commit e2f2bb269683d79cd6a12757aa140357fef089ad.

## Local evidence

- All five CLI commands; all four decisions; safe synthetic fixtures and failure injection.
- Exact artifact/policy identity, independent coverage, drift checks, private raw evidence and validated JSON/escaped Markdown.
- Lock/lint/format/security rules/types/tests and isolated wheel/sdist build.
- Fresh cached hash-locked runtime environment installs the wheel outside the checkout; real CLI scan/inspect/controls/invalid-schema checks pass with runtime socket connections denied.
- Real ModelScan 0.8.8 standalone inert-file proof on macOS; required memory-resource evidence remains unsupported, producing INSUFFICIENT as designed.
- Dependency/notice review and point-in-time OSV query; no matched advisories among 35 locked package/version pairs. This is not a security guarantee.

Exact final commands, counts, failed attempts and artifact checksums are in `verification/PH-10/`, `verification/MV-024/` through `verification/MV-029/`, and PROGRESS. Operational verification records are deliberately excluded from distribution archives; the local checkout retains them.

## Pending public-release gates

| Gate | Current state |
|---|---|
| Hosted Ubuntu/macOS CI | Workflow prepared and locally parsed; never dispatched. GitHub CLI is not authenticated. |
| Linux execution and resource limits | Implemented target; unverified locally; Linux-only memory test explicitly skipped on macOS. |
| Project review and risk acceptance | ADRs remain Proposed. Scanner is not containment, and memory/network/format limitations need explicit review before broader claims. |
| Version-controlled release checkpoint | Local source/docs are saved uncommitted; no new commit, tag or push made. |
| Public package/release | Not published; no automatic deployment/release workflow. |

Run the pinned hosted matrix and review the actual results before widening supported-platform claims. Review source, dependency notices, privacy and residual risks, then make a version-controlled release checkpoint and publish only when the public release checklist passes. No credentials or raw model artifacts should enter CI.

The PH-10 evidence above is the historical local candidate checkpoint. Subsequent PH-08/MV-020 work adds an optional offline advisory supplement; current build/test evidence is retained in verification/MV-020/. Benchmark research remains deferred. PH-11 loader execution remains gated and unimplemented. The local candidate has no benchmark superiority, legal clearance or universal model-safety claim.
