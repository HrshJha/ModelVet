# Mac preview v0.1.0-mac-preview.1

**Mac product complete:** static CLI and local Workbench meet the scoped FR-028/MV-045 gate. Local arm64 and hosted macOS 15 Intel acceptance pass: 628 Python tests, one Linux-only skip, seven components, 15 browser workflows and 13 repeated installed-package checks. Source hygiene is verified at 5cd322d in [run 39622723371](https://github.com/HrshJha/ModelVet/actions/runs/39622723371). Generated dependencies and browser session files are excluded from the release tree; the original external commit remains in history.

**Distribution record:** [Mac preview release](https://github.com/HrshJha/ModelVet/releases/tag/v0.1.0-mac-preview.1) is the designated handoff location for the wheel, source archive, bundle, installation notes and checksums. The release manifest records the exact merged source and byte identities. This is a limited GitHub prerelease, with no PyPI upload. Repository visibility remains unchanged (public when checked). Internal engineering acceptance is not independent certification.

**Deferred scope:** PH-08 independent comparative research and PH-11 Linux/KVM loader research remain deferred, not completed. They do not block the Mac static product. No model loading, containment or benchmark superiority is claimed. Required missing scanner/resource proof still yields INSUFFICIENT. See [Mac release specification](MAC_RELEASE_SPEC.md).

## Historical checkpoints

The dated records below describe earlier scopes and candidates; the Mac scope above governs this delivery.

**Mac preview acceptance passed:** FR-028/MV-045 is complete locally and on hosted macOS 15 Intel (run 39620134875, implementation a415a2d). Independent benchmark comparison and Linux/KVM loader research are deferred, not current delivery gates. The limited Mac preview may be published in the existing repository after integration; no independent certification or broader platform support is claimed.

**Current Mac-first scope (2026-10-21):** The maintainer narrowed the deliverable to the local static Mac CLI/Workbench. [MAC_RELEASE_SPEC](MAC_RELEASE_SPEC.md) controls this limited preview: required engineering/package checks apply; independent benchmark and Linux/KVM loader research are deferred and do not block it. Historical broader-release gates below remain applicable only if that broader scope is resumed. No independent review or loader validation is claimed.

**Current (2026-10-21):** PH-15–17 local workbench preview implemented; 622 local Python tests, seven components and 14 browser workflows pass, including installed-wheel launch without application Node/external sockets. Extended hosted Ubuntu/macOS execution passed at 996d19f (run 39611891146): 623 Python tests on Ubuntu, 622 plus one skip on macOS, seven components and 14 browser workflows each. Prior static hosted validation is recorded below. Public release, independent project/security review and PH-08/11 external evidence remain pending. Earlier checkpoint descriptions below are historical. See [workbench guide](WORKBENCH_GUIDE.md) and PROGRESS.

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
| Hosted Ubuntu/macOS CI | COMPLETE on Ubuntu 24.04 + macOS 15 Intel at 3d24c0a; run 39465563101 passes full tests/build/install/scanner contracts. |
| Linux execution and resource limits | Hosted Ubuntu 24.04 passes all 560 tests, including the Linux-only resource case; real inert scanner/resource proof completes. |
| Project review and risk acceptance | ADRs remain Proposed. Scanner is not containment, and memory/network/format limitations need explicit review before broader claims. |
| Version-controlled release checkpoint | Candidate commits are on codex/ci-release-gates / PR 1, including the CI fix and review packet. Final reviewed release checkpoint remains pending; no public tag/package. |
| Public package/release | Not published; no automatic deployment/release workflow. |

Run the pinned hosted matrix and review the actual results before widening supported-platform claims. Review source, dependency notices, privacy and residual risks, then make a version-controlled release checkpoint and publish only when the public release checklist passes. No credentials or raw model artifacts should enter CI.

The PH-10 evidence above is the historical local candidate checkpoint. Subsequent PH-08/MV-020 work adds an optional offline advisory supplement; current build/test evidence is retained in verification/MV-020/. A synthetic development pilot is INCONCLUSIVE; hidden holdout and independent adjudication remain pending. PH-11 loader execution remains gated and unimplemented. The local candidate has no benchmark superiority, legal clearance or universal model-safety claim.

The user explicitly selected leaving independent benchmark/security review and dedicated Linux/KVM gates pending while local validation finishes. PH-11 review preparation is documented in LOADER_REVIEW_PACKET.md; it enables no capability. Latest local corpus/pilot/package evidence is in verification/MV-023/.

## PH-12–14 local extension

The user selected “Extend the local feature plan.” Verify, compare and explicit-manifest batch audits now extend the local static report workflow. Current source/build/test identities and actual results are retained in `verification/MV-035/`; prior checkpoints above remain historical. No dependency, admission policy or loader capability changed. Hosted CI, Linux validation, independent review, public release and PH-11 gates remain pending.

## Current hosted validation evidence

[Run 39465563101](https://github.com/HrshJha/ModelVet/actions/runs/39465563101) passes both declared hosted targets at source 3d24c0a. The offline cache setup failure is fixed without relaxing release runtime guards; no dependency change. Actual job metadata/counts and log hashes are retained in verification/MV-026/hosted-followup/. Local macOS arm64 evidence remains separate from hosted Intel evidence. The reviewable candidate and outstanding acceptances are in [RELEASE_REVIEW_PACKET](RELEASE_REVIEW_PACKET.md). Public release remains blocked on the unfulfilled human/project review gate; PH-08/11 are separate.
