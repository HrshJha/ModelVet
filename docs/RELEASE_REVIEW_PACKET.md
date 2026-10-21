# Static/workbench preview review packet — acceptance pending

The user requested completion of PH-08–11. This packet separates actual candidate evidence from the external evidence still required. It records no reviewer approval and enables no loader capability.

## Current workbench preview — 2026-10-21

The PH-15–17 optional local workbench is implemented in [PR 3](https://github.com/HrshJha/ModelVet/pull/3), with source implementation `996d19f5af32ff1a89b770534e58e3c9d258a67a`. [Hosted run 39611891146](https://github.com/HrshJha/ModelVet/actions/runs/39611891146) passes Ubuntu 24.04 (623 Python tests) and macOS 15 Intel (622 plus one Linux-only skip), seven components and 14 browser workflows each, including installed-package acceptance. Subsequent evidence/documentation commits do not change application code. The earlier candidate/Unicode paragraphs below remain historical.

Review the new loopback authentication/Host/Origin/CSRF boundary, rooted path browser, private SQLite and pinned report reads, fixed own-worker argv/environment, cancellation/restart cleanup, untrusted-text rendering and optional dependency/distribution notices. See [WORKBENCH_SPEC](WORKBENCH_SPEC.md), [WORKBENCH_GUIDE](WORKBENCH_GUIDE.md), THREAT_MODEL and `verification/workbench/`. `preview-distributions.json` pins the retained local wheel/source archive; a reviewer must select exact reviewed source/package identities before publication. Synthetic demo reports and automated acceptance are not independent security review. The optional HTTP interface and persistent index expand the review scope beyond the original static CLI. All reviewer dispositions and proposed ADR acceptances remain pending.

## Candidate under review

**Subsequent correction (2026-10-20):** The MV-011 follow-up on branch `codex/evidence-unicode-keys`, based on `bdab77502cbb32591d1625de4e3afcc1abe28b1b`, rejects invalid Unicode keys in Python-created evidence. Review this source correction and its [verification records](verification/MV-011/unicode-keys/README.md) before accepting a candidate; `identities.json` records source and rebuilt distribution hashes. Its local suite passes 577 tests with one Linux-only skip. The hosted counts and commits below describe the earlier candidate and do not validate this correction.

- Repository: private HrshJha/ModelVet, candidate commit `feb9e8d2d980615af4b376a5bd26d89fd9f7f233` (CI cache correction on top of the full local static candidate).
- Review: [draft PR 1](https://github.com/HrshJha/ModelVet/pull/1).
- Hosted validation: [passing candidate Actions run](https://github.com/HrshJha/ModelVet/actions/runs/39465563101) at source 3d24c0a3810664c4cab4b760df5f207ff95cdf9a. Ubuntu 24.04 and macOS 15 Intel pass every step; actual job evidence is in verification/MV-026/hosted-followup/intel-results.json.
- Local gate: 559 passed, one explicit Linux-only skip; lock/lint/format/security/types pass. New-cache reproduction and 12 passing release/CI contracts are retained under verification/MV-026/hosted-followup/.
- No dependency addition or admission change. CI primes exported hash-locked runtime dependencies during setup; installation/runtime release checks remain offline/network-denied.

## Required project/security review

Review the proposed ADRs and source at the exact candidate commit. Each acceptance needs reviewer identity, date, source/config identities, examined evidence, residual risks and explicit disposition. An implementation agent's own tests/review cannot supply independent human acceptance. Do not sign a blank template or infer acceptance from a general request to complete the project.

| Topic | Concrete review evidence | Acceptance state |
|---|---|---|
| Host static safety | inventory/snapshot/structural readers; tests/test_security_invariants.py and test_resource_limits.py | Project review pending |
| External scanner boundary | scanners/modelscan.py, separate hash lock, resource checks and real inert smoke | Project risk acceptance pending |
| Admission integrity | coverage and evaluator, policy/config schemas, fail-closed/property/E2E cases | Project review pending |
| Report confidentiality/integrity | restricted writes, best-effort redaction, raw byte preservation, semantic digest and audit tests | Project review pending |
| Dependencies and distribution | uv.lock, notices under verification/MV-001/010/024, fresh installed-package tests and build identities | Project review pending |
| Public release target | fixed reviewed source, passing hosted checks and reviewed package hashes | Not published; destination/release acceptance pending |

Residual risks requiring explicit review include: exploitable scanner parsers execute as a host subprocess rather than a sandbox; scanner network isolation is not OS-enforced; Darwin cannot enforce required scanner memory limits; archive/member completeness remains unproven; unknown formats and declarations remain unresolved; filesystem rechecks are best effort; raw bytes/exact names/policy owners may contain sensitive information. ModelVet's default policy preserves these gaps as INSUFFICIENT where required. No universal safety, provenance authenticity or legal-clearance claim is offered.

## PH-08 research evidence still required

The ten-case synthetic development pilot is INCONCLUSIVE. Completion needs an independently controlled, unexamined holdout with provenance/license and frozen identities; a preregistered eligibility/method record; named independent adjudicators; real eligible baseline outputs; and a reviewed results/limitations record. Keep hidden cases outside this checkout and ordinary CI. Do not relabel development recipes or automated self-checks as independent held-out evidence. No superiority claim follows from current results.

## PH-11 laboratory and review still required

The current host is Darwin arm64 with no /dev/kvm or installed Linux runtime. A hosted static CI job is not a dedicated loader laboratory. Supply an operator-approved Linux/KVM host alias (no passwords/tokens in documentation), isolation review, patch inventory, approved pinned VMM/jailer/kernel/rootfs/framework identities, approved controlled fixtures, instrumentation negative tests and teardown evidence. The exact review questions and trial boundary are in [LOADER_REVIEW_PACKET](LOADER_REVIEW_PACKET.md). MV-030–032 remain gated; no runner can be enabled by changing this document.

## Sign-off record to be supplied by actual reviewers

For each acceptance, record: scope/task/ADR IDs; candidate source commit; configuration and evidence SHA-256 values; reviewer identity and independence; date; examined tests/observations; limitations and residual risk disposition; APPROVED / REJECTED / NEEDS CHANGES. Attach evidence through the project review process. Missing records stay pending; neither a hash nor a filled field authenticates a reviewer.
