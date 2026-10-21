# Open questions and uncertainty register

**Mac preview scope update:** OQ-09/10/13 remain unanswered research questions and are deferred; they do not block FR-028/MV-045 Mac completion. A separate Hugging Face URL feature is now proposed for the next release under PH-19/20; its client/network questions OQ-15–17 now have a local implementation decision recorded in HUB_ASSESSMENT_SPEC; external review/publication are separate. Current preview acceptance remains defined in [MAC_RELEASE_SPEC](MAC_RELEASE_SPEC.md). No independent review result is inferred from the scope change.

**Updated 2026-10-21.** This table is the current disposition. Original proposal cards and dated checkpoints below are historical evidence; they do not reopen resolved implementation questions. Independent review/research/loader questions remain open. All ADRs remain Proposed.

| ID | Question | Current disposition | Evidence / remaining requirement |
|---|---|---|---|
| OQ-01 | Exact compatible core/scanner/UI versions? | RESOLVED for declared targets | Core/ui uv.lock plus separate ModelScan 0.8.8 lock; fresh installs and Ubuntu/macOS CI pass. They deliberately use separate environments. |
| OQ-02 | Positive per-file/member coverage? | PARTIAL | Named standalone file proof observed; archive/member completeness remains INCONCLUSIVE. No inference from tool exit alone. |
| OQ-03 | Useful multi-GB snapshot budgets? | PARTIAL | Fixed ceilings and bounded synthetic resource measurements tested. Real multi-GB throughput/usability is unmeasured. |
| OQ-04 | Reliable mandatory metadata fields? | PARTIAL | Sourced LICENSE/PROVENANCE declarations and conflict handling implemented. Authenticity/legal rights are not established. |
| OQ-05 | Safe PyTorch ZIP interpretation? | PARTIAL | Bounded ZIP index subset implemented without torch. Loader reachability/equivalence remains unproven. |
| OQ-06 | Corroboration for prohibitions? | IMPLEMENTED; review pending | Owned inventory/classification/source-presence proof substantiates the configured source ban. Other scanner claims cannot independently BLOCK; tests pass. ADR/project review remains pending. |
| OQ-07 | Offline advisory evidence sufficient? | PARTIAL | Explicit exact-version snapshot supplement implemented; source authenticity, ranges, actual installed state and reachability remain unresolved. |
| OQ-08 | Supported OS matrix? | RESOLVED for declared targets | Ubuntu 24.04 and macOS 15 Intel pass full static/workbench CI; local macOS arm64 tested. Windows/other targets are unsupported. |
| OQ-09 | Operationally safe microVM research? | OPEN; external prerequisites | Dedicated approved Linux/KVM host, independent isolation review and fixed runtime identities not supplied. No loader implementation enabled. |
| OQ-10 | Held-out incremental value? | OPEN; independent research | Development pilot is INCONCLUSIVE. Hidden holdout, eligible alternatives and independent adjudication remain pending. |
| OQ-11 | Safe report destination? | IMPLEMENTED and tested | Explicit/default output separation, inode ancestry and edge/failure cases pass on supported targets. Filesystem race detection remains best effort. |
| OQ-12 | Sufficient scanner confinement? | PARTIAL; risk acceptance pending | Process caps tested; required Darwin memory evidence remains unsupported, and OS network isolation is not enforced. A subprocess is not a sandbox. |
| OQ-13 | Independently true discrepancy? | OPEN; independent research | Development byte-method agreement does not replace independent discrepancy/holdout adjudication. |
| OQ-14 | Dependency/fixture licenses? | INVENTORIED; scoped Mac prerelease published | Core/scanner/UI license metadata/notices retained; runtime notices bundled; generated inert fixtures use project MIT license. Broader product/risk review remains open if release claims expand. |
| OQ-15 | Can the selected official Hub client enforce endpoint/redirect/DNS/IP restrictions and byte/time ceilings? | RESOLVED LOCALLY; stdlib transport/1 | Reviewed official client 2.2.0; implemented direct stdlib HTTPS with tested exact-host/public-IP/DNS-pinning/stream limits instead of its auto-redirect/Xet/cache helpers. Independent certification is not claimed. |
| OQ-16 | Which retrieval and inventory limits are usable on supported Macs? | PARTIAL; conservative local settings tested | Byte/count/deadline/storage bounds pass synthetic failure tests and a small live 1/2 MiB run. Workbench defaults to 64/128 MiB; general multi-GB performance/usability remains unmeasured. |
| OQ-17 | Which Hub metadata identifiers establish revision/file identity and what do they cryptographically guarantee? | IMPLEMENTED CONSERVATIVELY; publisher trust unresolved | Full commit pin, native Git blob SHA-1 and documented LFS content SHA-256 checks, plus local SHA-256, are tested against fixtures/live transfers. Upstream assertions remain unauthenticated source claims; no publisher/safety attestation is inferred. |

Current published Mac release evidence: run [39624146859](https://github.com/HrshJha/ModelVet/actions/runs/39624146859) at `7e722c7c379bda6ec3dbc31feb38f3c7dc08e17e`; the earlier run 39613283917 is historical. See PROGRESS, THIRD_PARTY, RELEASE_REVIEW_PACKET and `verification/completion/` for the external research/loader gates. For the proposed Hub feature, see OQ-15–17. No question is closed by merely editing this register.

The working-tree Hub candidate implements MV-046–053. Local transport tests address OQ-15; OQ-16 remains a large-model performance/usability uncertainty, and OQ-17 preserves upstream trust limits. Official documentation and local tests do not establish independent security certification. No API credential was collected.

## Detailed uncertainty cards — historical proposal


### OQ-01 — What exact versions of hatchling, pytest, ruff, mypy and ModelScan resolve together under Python 3.12?
- **Status / owner:** OPEN; ModelVet maintainer.
- **Why it matters:** A noninstallable manifest blocks project start.
- **Available evidence:** Typer 0.27.3/Pydantic 2.14.1/uv 0.13.0 releases checked; ModelScan Python <=3.12 public claim.
- **Provisional assumption:** Pin verified stable versions at MV-001 and MV-010.
- **Risk if wrong:** Manifest incompatible or unsupported scanner.
- **How to resolve:** Resolve uv.lock; import smoke; scanner JSON/exit fixture suite.
- **Related tasks:** `MV-001`, `MV-010`; **decisions:** `ADR-002`, `ADR-006`.


### OQ-02 — Can ModelScan output establish positive coverage per individual file/member?
- **Status / owner:** OPEN; ModelVet maintainer.
- **Why it matters:** Central claim must not rely on guessed scanner coverage.
- **Available evidence:** Documented skipped flag and 0–4 exits; published issues report omissions.
- **Provisional assumption:** When proof absent, use INCONCLUSIVE.
- **Risk if wrong:** Many real scans cannot APPROVE.
- **How to resolve:** Inspect version-pinned JSON with diverse safe fixture set.
- **Related tasks:** `MV-010`, `MV-012`; **decisions:** `ADR-004`, `ADR-006`.


### OQ-03 — What snapshot budgets remain useful for multi-GB models?
- **Status / owner:** OPEN; ModelVet maintainer.
- **Why it matters:** Copying large models may be prohibitive.
- **Available evidence:** Proposed 1GiB/file,2GiB total; no empirical performance.
- **Provisional assumption:** Scope v0.1 to small supported models.
- **Risk if wrong:** Most practical artifacts unsupported.
- **How to resolve:** Test bounded file sizes; measure disk+time; adjust only with threat review.
- **Related tasks:** `MV-004`, `MV-025`; **decisions:** `ADR-003`.


### OQ-04 — Which local license/provenance fields are reliable enough to make mandatory?
- **Status / owner:** OPEN; ModelVet maintainer.
- **Why it matters:** Overly strict default may always return INSUFFICIENT.
- **Available evidence:** HF cards and README claims can conflict.
- **Provisional assumption:** Record as sourced declarations; default policy narrowly scopes required fields.
- **Risk if wrong:** Unusable false uncertainty or false legal clearance.
- **How to resolve:** Review representative local directories and legal disclaimer.
- **Related tasks:** `MV-008`, `MV-015`; **decisions:** `ADR-008`.


### OQ-05 — Can the tool distinguish PyTorch ZIP checkpoint members safely without importing torch?
- **Status / owner:** OPEN; ModelVet maintainer.
- **Why it matters:** Scanner-loader mismatch may depend on loader internals.
- **Available evidence:** ZIP index is inspectable, but semantics are version dependent.
- **Provisional assumption:** Treat index inspection as structural only.
- **Risk if wrong:** Incorrectly label reachable entry as unreachable.
- **How to resolve:** Design independent controlled oracle P1/P2.
- **Related tasks:** `MV-007`, `MV-022`, `MV-031`; **decisions:** `ADR-009`, `ADR-010`.


### OQ-06 — How should a PROHIBITED policy rule be corroborated?
- **Status / owner:** OPEN; ModelVet maintainer.
- **Why it matters:** BLOCK before incompleteness must be grounded.
- **Available evidence:** Policy precedence proposed in PRD.
- **Provisional assumption:** Only independent inventory/structural fact or reviewed corroboration can BLOCK.
- **Risk if wrong:** False blocks or false approvals.
- **How to resolve:** Adversarial policy property test cases.
- **Related tasks:** `MV-014`, `MV-019`; **decisions:** `ADR-005`.


### OQ-07 — Is offline OSV matching sufficient for dependency vulnerability evidence?
- **Status / owner:** OPEN; ModelVet maintainer.
- **Why it matters:** Stale snapshot can mislead users.
- **Available evidence:** OSV version-query API docs verified.
- **Provisional assumption:** Use user-supplied timestamped snapshot P1.
- **Risk if wrong:** Outdated or inexact matching.
- **How to resolve:** Fixture affected/unaffected versions + stale feed tests.
- **Related tasks:** `MV-020`; **decisions:** `ADR-008`.


### OQ-08 — What supported OS matrix is practical?
- **Status / owner:** OPEN; ModelVet maintainer.
- **Why it matters:** Process limits and filesystem semantics differ.
- **Available evidence:** Pure Python can run POSIX; actual tests absent.
- **Provisional assumption:** Start Linux/macOS; Windows unverified.
- **Risk if wrong:** Hidden platform bypass.
- **How to resolve:** Run CI matrix and manual filesystem race review.
- **Related tasks:** `MV-026`; **decisions:** `ADR-002`.


### OQ-09 — Is safe microVM execution operationally feasible for one developer?
- **Status / owner:** OPEN; ModelVet maintainer + independent security reviewer.
- **Why it matters:** Host compromise/isolation errors unacceptable.
- **Available evidence:** Firecracker guidance prescribes KVM/jailer/seccomp/cgroups.
- **Provisional assumption:** P2 only on dedicated Linux test host.
- **Risk if wrong:** High-maintenance unsafe project.
- **How to resolve:** Independent sandbox review and negative containment tests.
- **Related tasks:** `MV-030`; **decisions:** `ADR-009`.


### OQ-10 — Does a head-to-head benchmark show incremental held-out value vs Layerfault/PickleBall/ModelScan?
- **Status / owner:** OPEN; ModelVet maintainer.
- **Why it matters:** No USP without comparisons.
- **Available evidence:** Relevant alternatives already have security coverage.
- **Provisional assumption:** Avoid advantage claims until paired controlled tests.
- **Risk if wrong:** Duplicate product with no technical increment.
- **How to resolve:** Run blinded matched-scope benchmark, adjudicate.
- **Related tasks:** `MV-022`, `MV-023`; **decisions:** `ADR-010`.


### OQ-11 — Will default report destination work on all intended hosts without input overlap?
- **Status / owner:** OPEN; ModelVet maintainer.
- **Why it matters:** Output could contaminate artifact hash.
- **Available evidence:** XDG-style proposed default `~/.local/state/...`.
- **Provisional assumption:** Reject overlap and support explicit --out.
- **Risk if wrong:** Nonportable default or hidden overwrite.
- **How to resolve:** Linux/macOS CLI tests with home/path edge cases.
- **Related tasks:** `MV-003`, `MV-016`; **decisions:** `ADR-007`.


### OQ-12 — Can scanner invocation be sufficiently constrained without a VM?
- **Status / owner:** OPEN; ModelVet maintainer + independent security reviewer.
- **Why it matters:** Scanner parser exploitation can compromise host.
- **Available evidence:** Subprocess is not a sandbox.
- **Provisional assumption:** No model execution; process caps and disclosure; honest risk.
- **Risk if wrong:** Host vulnerability from malformed sample.
- **How to resolve:** Threat-model review, process limits, optional separate scanner VM.
- **Related tasks:** `MV-010`, `MV-024`; **decisions:** `ADR-006`, `ADR-009`.


### OQ-13 — What constitutes an independent true discrepancy rather than an unsupported format?
- **Status / owner:** OPEN; ModelVet maintainer.
- **Why it matters:** Overstates scanner superiority.
- **Available evidence:** Issues #218/#354 and loader-specific facts.
- **Provisional assumption:** Paired supported tests only; unknown not counted baseline failure.
- **Risk if wrong:** Artificial boost in false-clean metrics.
- **How to resolve:** Fixture oracle reviewed by two methods.
- **Related tasks:** `MV-022`, `MV-023`; **decisions:** `ADR-010`.


### OQ-14 — What licenses apply to all selected direct and transitive packages and fixtures?
- **Status / owner:** OPEN; ModelVet maintainer.
- **Why it matters:** Public redistribution requirements.
- **Available evidence:** Package pages are not complete dependency license inventory.
- **Provisional assumption:** Audit during lock/release, exclude problematic fixture.
- **Risk if wrong:** Distribution/license risk.
- **How to resolve:** Read SPDX metadata and LICENSE/NOTICE, document legal uncertainty.
- **Related tasks:** `MV-001`, `MV-029`; **decisions:** `ADR-002`.

## MV-001 evidence update — 2026-10-20

OQ-01 is partially resolved: the Python 3.12 foundation resolves, installs and builds on macOS with exact tool versions in the manifest/lock. ModelScan and Linux remain unverified. OQ-14 is partially resolved: the current 30-package lock has saved wheel license/notice and advisory evidence in `verification/MV-001/`; future dependencies, fixture rights and release redistribution remain to audit.

## PH-04 evidence update — 2026-10-20

OQ-01: core and ModelScan 0.8.8 resolve in separate locks/environments; real smoke passes on macOS, Linux remains pending. OQ-02: pinned JSON positively names standalone scanned files and skipped paths; archive member completeness remains inconclusive. OQ-12: Darwin memory APIs reject tested caps; remaining process limits are enforced, memory coverage stays UNSUPPORTED and network isolation is not asserted. OQ-14: separate scanner dependency notices/advisories are inventoried, including bundled NumPy licenses; redistribution review remains a release gate.

## PH-05 evidence update — 2026-10-20

OQ-06 has a tested conservative v1 implementation: only complete owned inventory/classification/source-presence proof substantiates a configured repository-code prohibition. Scanner severity or verification labels remain insufficient, and unbound integrity conflicts prevent a ban. Property/status tests pass; full scan E2E in MV-019 and explicit ADR/project review remain outstanding, so this does not close the question or accept ADR-005. The default requires sourced LICENSE/PROVENANCE declarations without treating them as verified legal or lineage facts.

## Local PH-10 candidate update

OQ-01: core and separate scanner locks install/build on macOS; hosted/Linux validation pending. OQ-02: named standalone-file proof observed, archive member completeness remains inconclusive. OQ-03: bounded synthetic resource measurements are recorded in MV-025, not real multi-GB throughput. OQ-06: full CLI/property/fault cases verify independent inventory bans; explicit ADR/project review remains pending. OQ-12: Darwin memory enforcement and OS network isolation remain unavailable; no loader capability is enabled. OQ-14: core/scanner notices, fixture rights and package contents reviewed for the local candidate; THIRD_PARTY records sources. No optional benchmark or independent isolation claim is closed by these local results.

## MV-020 evidence update — 2026-10-20

OQ-07 has a conservative offline implementation: exact PyPI enumerated-version matching from explicit query snapshots, timestamp/size/schema/identity checks and missing/unsupported fail-closed supplemental gates. Authentic publisher freshness/completeness, version ranges, actual installation and exploitability remain unverified; no global vulnerability clearance is claimed. Project review is still pending.

## MV-022/023 and PH-11 readiness update — 2026-10-20

OQ-10/13 remain open: ten method-checked inert development recipes and a real pinned scanner pilot exist, but no hidden holdout/independent discrepancy adjudication or eligible alternative-tool experiment establishes incremental detection. Study status is INCONCLUSIVE. OQ-09 remains open: current host is Darwin without KVM/Firecracker/jailer; no reviewed dedicated Linux host was supplied. User selected leaving independent research/security/Linux gates pending while completing local validation. Proposed review preparation is LOADER_REVIEW_PACKET.md; no execution is enabled.


Hub local candidate update: no cache is enabled; no third-party Hub dependency is added and Python 3.12 remains supported. The current working tree implements CLI and Workbench URL input; the published preview remains local-folder-only. HF_TOKEN is used only after explicit selection; no credentials were collected.
