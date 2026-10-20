# Local v0.1.0 candidate and release gates

The user selected **“Finish local candidate; leave hosted CI pending.”** PH-06/07 and the local portions of PH-09/10 are implemented. This is not a public release, hosted CI pass or independent security certification. Work started at e2f2bb269683d79cd6a12757aa140357fef089ad. A newer local checkpoint af86ffee5c7b4f1e990e9dbbdba6625e973acef0 appeared outside agent commands; checkpoint b91a791c6c3b4137a39fb540822e888d54948549 was observed later; final working-tree/source identities are recorded in verification/MV-023/.

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
| Version-controlled release checkpoint | Local checkpoints af86ffee/b91a791c exist; final source/worktree identities are recorded in verification/MV-023/. Final reviewed release checkpoint is pending; no agent commit/tag/push made. |
| Public package/release | Not published; no automatic deployment/release workflow. |

Run the pinned hosted matrix and review the actual results before widening supported-platform claims. Review source, dependency notices, privacy and residual risks, then make a version-controlled release checkpoint and publish only when the public release checklist passes. No credentials or raw model artifacts should enter CI.

The PH-10 evidence above is the historical local candidate checkpoint. Subsequent PH-08/MV-020 work adds an optional offline advisory supplement; current build/test evidence is retained in verification/MV-020/. A synthetic development pilot is INCONCLUSIVE; hidden holdout and independent adjudication remain pending. PH-11 loader execution remains gated and unimplemented. The local candidate has no benchmark superiority, legal clearance or universal model-safety claim.

The user explicitly selected leaving independent benchmark/security review and dedicated Linux/KVM gates pending while local validation finishes. PH-11 review preparation is documented in LOADER_REVIEW_PACKET.md; it enables no capability. Latest local corpus/pilot/package evidence is in verification/MV-023/.
