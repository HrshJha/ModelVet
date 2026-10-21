# Research and primary-source register

**Accessed/rechecked 2026-10-20** using publicly available documentation, code and issues. URLs are direct source links. Research is not an implementation test. Repo HEAD and product offerings may change; lock source commit/version before reproducing specific behavior. Distinguish **public documentation**, **user issue allegations**, and **measured experimental results**. Findings in earlier four reports were compared, not taken as proven by repetition.

| Ref | Source | Primary publisher | URL | Finding / verified scope |
|---|---|---|---|---|
| R-01 | ModelScan README | Protect AI GitHub | https://github.com/protectai/modelscan | Supported scanning formats and Python 3.9–3.12, CLI examples |
| R-02 | ModelScan CLI implementation | Protect AI GitHub | https://github.com/protectai/modelscan/blob/main/modelscan/cli.py | Exit codes 0=none,1=findings,2=errors,3=unsupported,4=usage, JSON reports |
| R-03 | ModelScan issue #354 | Protect AI GitHub issue | https://github.com/protectai/modelscan/issues/354 | Reporter alleges ZIP iteration can stop before a later member and yield misleading no-findings |
| R-04 | ModelScan issue #218 | Protect AI GitHub issue | https://github.com/protectai/modelscan/issues/218 | Skipped file accompanied by No issues found language and skipped count |
| R-05 | Transformers security policy | Hugging Face GitHub | https://github.com/huggingface/transformers/blob/main/SECURITY.md | Recommend safetensors and revision pinning; caution custom model code |
| R-06 | Transformers model loading docs | Hugging Face | https://huggingface.co/docs/transformers/models | Custom models may require trust_remote_code, pinned revision recommended |
| R-07 | PyTorch serialization semantics | PyTorch docs | https://docs.pytorch.org/docs/stable/notes/serialization.html | weights_only narrows RCE but DoS/memory risks remain |
| R-08 | Safetensors format specification | Hugging Face GitHub | https://github.com/safetensors/safetensors/blob/main/README.md | Header length, offsets and metadata format |
| R-09 | Hugging Face pickle scanner docs | Hugging Face | https://huggingface.co/docs/hub/security-pickle | Pickle import scanning best-effort and not foolproof |
| R-10 | Hugging Face malware scanner docs | Hugging Face | https://huggingface.co/docs/hub/security-malware | Files scanned; missing badges can mean queued/error |
| R-11 | PickleBall project | Columbia GitHub | https://github.com/columbia/pickleball | Static policy generator and load-time pickle enforcer |
| R-12 | Layerfault project | izm1chael GitHub | https://github.com/izm1chael/layerfault | Claims offline static checking and optional sandbox runtime probes; status release candidate |
| R-13 | JFrog scan local ML models | JFrog docs | https://docs.jfrog.com/security/docs/scan-your-ml-models | jf malicious-scan with formats, output types and AI Catalog policy |
| R-14 | OSV API query | Google OSV GitHub | https://github.com/google/osv.dev/blob/master/docs/api/post-v1-query.md | Version and package matching, API pagination |
| R-15 | Firecracker production host setup | Firecracker GitHub | https://github.com/firecracker-microvm/firecracker/blob/main/docs/prod-host-setup.md | KVM, seccomp, jailer, cgroups and patching prerequisites |
| R-16 | uv releases | Astral GitHub | https://github.com/astral-sh/uv/releases | uv 0.13.0 released 2026-10-09 |
| R-17 | Typer PyPI project | PyPI | https://pypi.org/project/typer/ | Typer 0.27.3 published 2026-10-06 |
| R-18 | Pydantic PyPI project | PyPI | https://pypi.org/project/pydantic/ | Pydantic 2.14.1 published 2026-10-11 |
| R-19 | Hypothesis PyPI project | PyPI | https://pypi.org/project/hypothesis/ | Hypothesis 6.170.5 published 2026-10-20 |
| R-20 | CycloneDX ML-BOM specification | OWASP CycloneDX | https://github.com/CycloneDX/specification | Standard supports ML-BOM transparency |

## Evidence details, limitations and resulting decisions

### R-01 — ModelScan README
- **Source / publisher:** Protect AI GitHub; **URL:** https://github.com/protectai/modelscan; **date accessed:** 2026-10-20.
- **Relevant section / claim:** Supported scanning formats and Python 3.9–3.12, CLI examples.
- **Establishes:** Explains current published coverage and installation.
- **Does not establish:** Does not prove zero false negatives or all artifact members actually scanned.
- **ModelVet consequence:** ModelScan subprocess only; exact version smoke test MV-010.

### R-02 — ModelScan CLI implementation
- **Source / publisher:** Protect AI GitHub; **URL:** https://github.com/protectai/modelscan/blob/main/modelscan/cli.py; **date accessed:** 2026-10-20.
- **Relevant section / claim:** Exit codes 0=none,1=findings,2=errors,3=unsupported,4=usage, JSON reports.
- **Establishes:** Confirms published implementation of exit behavior.
- **Does not establish:** Does not guarantee equivalent behavior in every old/new release.
- **ModelVet consequence:** Adapter maps exits; requires version pin.

### R-03 — ModelScan issue #354
- **Source / publisher:** Protect AI GitHub issue; **URL:** https://github.com/protectai/modelscan/issues/354; **date accessed:** 2026-10-20.
- **Relevant section / claim:** Reporter alleges ZIP iteration can stop before a later member and yield misleading no-findings.
- **Establishes:** Concrete issue report with reproduction discussion.
- **Does not establish:** Not independently retested in this documentation phase; upstream may fix.
- **ModelVet consequence:** Coverage reconciliation must not trust summary alone.

### R-04 — ModelScan issue #218
- **Source / publisher:** Protect AI GitHub issue; **URL:** https://github.com/protectai/modelscan/issues/218; **date accessed:** 2026-10-20.
- **Relevant section / claim:** Skipped file accompanied by No issues found language and skipped count.
- **Establishes:** Firsthand report of interpretability hazard.
- **Does not establish:** Does not claim scanner lacks skipped indicators or exit handling.
- **ModelVet consequence:** Always separate result from completeness.

### R-05 — Transformers security policy
- **Source / publisher:** Hugging Face GitHub; **URL:** https://github.com/huggingface/transformers/blob/main/SECURITY.md; **date accessed:** 2026-10-20.
- **Relevant section / claim:** Recommend safetensors and revision pinning; caution custom model code.
- **Establishes:** Documents model-consumer threat and safer settings.
- **Does not establish:** Not universal security proof.
- **ModelVet consequence:** MVP avoids loading.

### R-06 — Transformers model loading docs
- **Source / publisher:** Hugging Face; **URL:** https://huggingface.co/docs/transformers/models; **date accessed:** 2026-10-20.
- **Relevant section / claim:** Custom models may require trust_remote_code, pinned revision recommended.
- **Establishes:** Shows loader/version configuration matters.
- **Does not establish:** Not a reproducible exploit.
- **ModelVet consequence:** P2 scope pins exact context.

### R-07 — PyTorch serialization semantics
- **Source / publisher:** PyTorch docs; **URL:** https://docs.pytorch.org/docs/stable/notes/serialization.html; **date accessed:** 2026-10-20.
- **Relevant section / claim:** weights_only narrows RCE but DoS/memory risks remain.
- **Establishes:** Supports not relying on restricted unpickler as absolute sandbox.
- **Does not establish:** Not claim PyTorch always unsafe.
- **ModelVet consequence:** Do not host-side load.

### R-08 — Safetensors format specification
- **Source / publisher:** Hugging Face GitHub; **URL:** https://github.com/safetensors/safetensors/blob/main/README.md; **date accessed:** 2026-10-20.
- **Relevant section / claim:** Header length, offsets and metadata format.
- **Establishes:** Primary static header parser specification.
- **Does not establish:** Does not certify surrounding repository code.
- **ModelVet consequence:** bounded structural inspector.

### R-09 — Hugging Face pickle scanner docs
- **Source / publisher:** Hugging Face; **URL:** https://huggingface.co/docs/hub/security-pickle; **date accessed:** 2026-10-20.
- **Relevant section / claim:** Pickle import scanning best-effort and not foolproof.
- **Establishes:** Direct primary caveat on scanner interpretation.
- **Does not establish:** Does not quantify current bypass rate.
- **ModelVet consequence:** Scope report limitations.

### R-10 — Hugging Face malware scanner docs
- **Source / publisher:** Hugging Face; **URL:** https://huggingface.co/docs/hub/security-malware; **date accessed:** 2026-10-20.
- **Relevant section / claim:** Files scanned; missing badges can mean queued/error.
- **Establishes:** Shows platform alternatives and incomplete states.
- **Does not establish:** Does not prove all published files are safe.
- **ModelVet consequence:** Competitive context.

### R-11 — PickleBall project
- **Source / publisher:** Columbia GitHub; **URL:** https://github.com/columbia/pickleball; **date accessed:** 2026-10-20.
- **Relevant section / claim:** Static policy generator and load-time pickle enforcer.
- **Establishes:** Meaningful load-time security competitor.
- **Does not establish:** Does not guarantee all formats/frameworks.
- **ModelVet consequence:** Benchmark only on supported pickle workflows.

### R-12 — Layerfault project
- **Source / publisher:** izm1chael GitHub; **URL:** https://github.com/izm1chael/layerfault; **date accessed:** 2026-10-20.
- **Relevant section / claim:** Claims offline static checking and optional sandbox runtime probes; status release candidate.
- **Establishes:** Closest open-source overlap.
- **Does not establish:** Repository description is not independent production benchmark.
- **ModelVet consequence:** Do not claim sandbox novelty.

### R-13 — JFrog scan local ML models
- **Source / publisher:** JFrog docs; **URL:** https://docs.jfrog.com/security/docs/scan-your-ml-models; **date accessed:** 2026-10-20.
- **Relevant section / claim:** jf malicious-scan with formats, output types and AI Catalog policy.
- **Establishes:** Shows established pre-load scanning and competitive strength.
- **Does not establish:** Product docs not independent security efficacy.
- **ModelVet consequence:** Not a generic scanner USP.

### R-14 — OSV API query
- **Source / publisher:** Google OSV GitHub; **URL:** https://github.com/google/osv.dev/blob/master/docs/api/post-v1-query.md; **date accessed:** 2026-10-20.
- **Relevant section / claim:** Version and package matching, API pagination.
- **Establishes:** Advisory schema reference.
- **Does not establish:** No inference of exploit reachability.
- **ModelVet consequence:** P1 offline snapshot matcher.

### R-15 — Firecracker production host setup
- **Source / publisher:** Firecracker GitHub; **URL:** https://github.com/firecracker-microvm/firecracker/blob/main/docs/prod-host-setup.md; **date accessed:** 2026-10-20.
- **Relevant section / claim:** KVM, seccomp, jailer, cgroups and patching prerequisites.
- **Establishes:** Grounds P2 isolation prerequisites.
- **Does not establish:** No zero VM escape guarantee.
- **ModelVet consequence:** No behavior testing in MVP.

### R-16 — uv releases
- **Source / publisher:** Astral GitHub; **URL:** https://github.com/astral-sh/uv/releases; **date accessed:** 2026-10-20.
- **Relevant section / claim:** uv 0.13.0 released 2026-10-09.
- **Establishes:** Specific package-manager baseline verified.
- **Does not establish:** No dependency-graph check here.
- **ModelVet consequence:** Propose version, smoke during MV-001.

### R-17 — Typer PyPI project
- **Source / publisher:** PyPI; **URL:** https://pypi.org/project/typer/; **date accessed:** 2026-10-20.
- **Relevant section / claim:** Typer 0.27.3 published 2026-10-06.
- **Establishes:** Verified published version for CLI dependency.
- **Does not establish:** Not tested with ModelVet/Pydantic combo.
- **ModelVet consequence:** MV-001 lock proof.

### R-18 — Pydantic PyPI project
- **Source / publisher:** PyPI; **URL:** https://pypi.org/project/pydantic/; **date accessed:** 2026-10-20.
- **Relevant section / claim:** Pydantic 2.14.1 published 2026-10-11.
- **Establishes:** Verified published version for schema dependency.
- **Does not establish:** Not tested with selected Python+Typer combo.
- **ModelVet consequence:** MV-001 lock proof.

### R-19 — Hypothesis PyPI project
- **Source / publisher:** PyPI; **URL:** https://pypi.org/project/hypothesis/; **date accessed:** 2026-10-20.
- **Relevant section / claim:** Hypothesis 6.170.5 published 2026-10-20.
- **Establishes:** Verified release available for CPython 3.12.
- **Does not establish:** Not installed or run.
- **ModelVet consequence:** P0 property-test library.

### R-20 — CycloneDX ML-BOM specification
- **Source / publisher:** OWASP CycloneDX; **URL:** https://github.com/CycloneDX/specification; **date accessed:** 2026-10-20.
- **Relevant section / claim:** Standard supports ML-BOM transparency.
- **Establishes:** Potential future interoperability.
- **Does not establish:** No requirement to implement full BOM in MVP.
- **ModelVet consequence:** Defer BOM export.

## Competitive corrections and conflicting evidence

- ModelScan's issue #218 reports potentially misleading prose, **while the issue explicitly acknowledges a nonzero status and visible skipped count**. Therefore it would be false to claim the tool exposes no skipped-file evidence; ModelVet's advantage remains hypothesis.
- Issue #354 is a public vulnerability report. It should be marked **researcher-reported, reproduction not independently run in this task**, and rechecked against a specifically pinned tool release before inclusion in any published benchmark.
- JFrog and Layerfault already perform portions of model security beyond basic metadata analysis; generic scanning, sandboxing and approval reports are not unique.
- Hugging Face discourages unsafe model loading; safetensors reduces serialization attack surface but does not validate all repository code or native loader vulnerabilities.
- ModelScan's README supports Python 3.9–3.12, influencing ModelVet 3.12 baseline. The selected 2026 Python ecosystem may have newer releases but that is not permission to assume ModelScan is compatible with them.
- All academic figures from the earlier research (e.g., scanner-evasion rates) require benchmark-specific interpretation. ModelVet must not claim those figures as its own performance or universal attack rates.

## Known sources NOT exhaustively investigated

### MV-001 dependency evidence — 2026-10-20

The version-specific PyPI JSON URLs saved in `verification/MV-001/dependency-metadata.json` are primary package-publisher metadata, not independent security findings. Installed wheel LICENSE/NOTICE files (and the hash-verified colorama wheel, which is not installed on macOS) are preserved in `license-files.json` and `third-party-license-texts.txt`. The [OSV batch-query API](https://google.github.io/osv.dev/api/#operation/OSV_QueryBatch) response is saved beside its exact package/version query. Neither PyPI nor OSV returned advisory matches for this dependency snapshot; this does not establish absence of vulnerabilities. No artifact bytes or credentials were submitted. Toolchain setup and dependency review use network access during development; this is not an implemented runtime network feature.

Current open-source tool license compatibilities; every dependency's exact release/CI metadata; commercial JFrog/Protect AI side-by-side effectiveness; accurate model loader behavior across multiple framework versions; complete Hugging Face license lineage; Windows behavior; customer willingness to pay. These must be recorded as unresolved, not inferred.

## MV-007 parser sources — accessed 2026-10-20

- R-08 refreshed: [safetensors format](https://github.com/safetensors/safetensors/blob/main/README.md#format), header/offset structure; no tensor-loader testing performed.
- R-21: [PKWARE APPNOTE 6.3.10](https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT), local/central directory/end records (sections 4.3.7, 4.3.12, 4.3.16). Referenced for parser implementation; document is not redistributed. Scope restrictions and test evidence are recorded in ADR implementation notes and `verification/MV-007/`.

## MV-010 pinned scanner evidence — 2026-10-20

Version-pinned [ModelScan 0.8.8 publisher metadata](https://pypi.org/pypi/modelscan/0.8.8/json) and hash-verified wheel source were inspected for CLI exits, JSON reports, scanned/skipped generation and issue fields. Exact dependency metadata and OSV query/response are saved under `verification/MV-010/`; no advisory matches were returned, which does not prove absence of vulnerabilities. A generated benign None-pickle fixture was scanned in a separate process, without host deserialization; raw output shows named file coverage but does not establish archive-member completeness or malware detection efficacy.

## MV-026 CI implementation sources — accessed 2026-10-20

- R-22: [GitHub-hosted runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners), selected ubuntu-24.04 and macos-15 targets. This documents available targets, not executed ModelVet results.
- R-23: [Official checkout v7.0.1 source](https://github.com/actions/checkout/tree/3d3c42e5aac5ba805825da76410c181273ba90b1), immutable action definition and license metadata saved in verification/MV-026/actions.json.
- R-24: [Official setup-uv v10.3.0 source](https://github.com/astral-sh/setup-uv/tree/1c37ad07a6a961277cf70c0d37d6f313000f5884) and [uv CI guidance](https://docs.astral.sh/uv/guides/integration/github/); uv runtime pinned independently to 0.13.3. Hosted execution remains pending by user-selected scope.

## MV-020 OSV input contract — accessed 2026-10-20

- R-25: [Official OSV schema specification](https://github.com/ossf/osv-schema/blob/main/docs/schema.md), observed version 1.9.2; affected versions/ranges, withdrawn and schema compatibility semantics. The rendered schema URL failed to fetch; the official raw repository document was read. This is a format specification, not independent vulnerability evidence.
- [Official OSV query API](https://google.github.io/osv.dev/post-v1-query/) documents query input and vulnerability responses. ModelVet consumes operator-supplied offline envelopes only, with explicit per-query completeness. No runtime query client or live advisory feed is implemented. Example IDs/package/version records are synthetic and are not OSV findings.

## PH-11 review preparation — accessed 2026-10-20

R-26: official Firecracker [host setup](https://github.com/firecracker-microvm/firecracker/blob/main/docs/prod-host-setup.md), [jailer](https://github.com/firecracker-microvm/firecracker/blob/main/docs/jailer.md) and [design](https://github.com/firecracker-microvm/firecracker/blob/main/docs/design.md) documents were read for a proposed review packet. These are project guidance, not independent tests or ModelVet containment evidence. No hypervisor/framework/kernel/rootfs version is selected or installed, and no loader capability is enabled. The main-branch documents must be refreshed/pinned during actual independent review.

## MV-023 pilot interpretation

The real ModelScan 0.8.8 run used only locally generated inert bytes. Raw vendor output/report metadata is retained privately. It is direct execution evidence about this configuration and these development cases, not independent benchmark ground truth, malware detection efficacy or loader equivalence. No published vulnerability payload was reproduced.

## Hosted runner labels — 2026-10-20

[GitHub-hosted runners reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) documents macos-15 as ARM and macos-15-intel as the standard Intel macOS 15 target. This is vendor operational documentation, not independent security evidence or a completed execution. MV-026 actual Ubuntu/macOS results are stored separately under verification/MV-026/hosted-followup/.

## Workbench implementation references — primary vendor documentation

- [Vite backend integration](https://vite.dev/guide/backend-integration.html): bundled asset integration; vendor documentation, not independent security evidence.
- [FastAPI static files](https://fastapi.tiangolo.com/tutorial/static-files/): serving local assets through the Python service.
- [Playwright browser installation](https://playwright.dev/docs/browsers): pinned development browser installation; the application itself needs no Node runtime.
- [Official setup-node action](https://github.com/actions/setup-node/tree/249970729cb0ef3589644e2896645e5dc5ba9c38): pinned CI runtime setup; commit verified against official v6 ref on 2026-10-21.

Local tests establish only the bounded behaviors exercised. Dependency metadata, vendor specifications and automated accessibility checks are not independent product/security/accessibility certification.

## Hugging Face repository assessment proposal — accessed 2026-10-21

- **R-27 — Hub API and repository metadata.** [Hugging Face Hub Python API reference](https://huggingface.co/docs/huggingface_hub/en/package_reference/hf_api) documents `model_info` with a `revision`, `list_repo_files`, `list_repo_tree` and file metadata such as size/blob/LFS attributes when requested. `list_repo_tree` can enumerate a selected revision. This establishes documented client interfaces and optional metadata fields, not that upstream metadata is authoritative, complete, an integrity guarantee or safe. Architectural consequence: inventory by canonical repo ID and resolved commit; record absent metadata as unknown.
- **R-28 — Revision-aware retrieval.** [Hugging Face download guide](https://huggingface.co/docs/huggingface_hub/en/guides/download) documents `hf_hub_download` for individual files, a `revision` argument accepting branches/tags/full commit IDs, and version-aware caching. The guide says commit hashes should be full length. It also documents `snapshot_download` plus include/exclude patterns; those patterns do not prove ModelVet fetched only the check-required explicit paths. Consequence: use explicit one-file retrieval at the resolved commit; do not default to whole-repository download or trust cache alone.
- **R-29 — Local authentication and private/gated access.** [Authentication quickstart](https://huggingface.co/docs/huggingface_hub/en/quick-start#authentication) documents local token login and the `HF_TOKEN` environment variable; [user access token security](https://huggingface.co/docs/hub/security-tokens) describes fine-grained/read use and minimizing leaked-token impact; [gated model docs](https://huggingface.co/docs/hub/en/models-gated) state users must request/receive access and scripts need a user token to download. These are vendor access semantics, not a request for ModelVet to collect secrets. Consequence: public repositories require no credential; allow only explicit local user-selected authentication for authorized private/gated files, never include secrets in reports/logs/URLs.
- **R-30 — Python compatibility.** [Hub client installation documentation](https://huggingface.co/docs/huggingface_hub/en/installation) says the library is tested on Python 3.9+. Python 3.12 is therefore inside that documented range. This is not a tested ModelVet dependency combination or current-version pin. Consequence: exact client version, license/transitive review, Python/macOS lock compatibility, and network-boundary behavior remain tasks MV-046/047.

Accessed 2026-10-21. Vendor documentation can change; verify against a versioned documentation/source snapshot when selecting an exact package. The Hub API docs do not establish adequate SSRF/redirect/IP controls, complete inventory guarantees, content authenticity, availability/rate limits or safe assessment. No live repository or credential was used for this specification.

## Hub implementation review sources — 2026-10-21

- **R-31:** [Official Hub REST/OpenAPI](https://huggingface.co/.well-known/openapi.json), [API documentation](https://huggingface.co/docs/hub/api): revision-aware model metadata/tree and resolve endpoints; vendor interface documentation, not independent security evidence.
- **R-32:** [Official client 2.2.0 file_download.py](https://github.com/huggingface/huggingface_hub/blob/v2.2.0/src/huggingface_hub/file_download.py), [HTTP utilities](https://github.com/huggingface/huggingface_hub/blob/v2.2.0/src/huggingface_hub/utils/_http.py): local source review found default auto-follow clients and separate Xet/cache paths. Captured SHA-256: file_download.py `40c2b3156162ae9996f03badbce9196979bf874219faa0da43bc39cee8162512`; utils/_http.py `4bd06341e5233296bb70f856218d8ecbe013f3845daa078fcd01268d80d2a6c9`. The library was evaluated, not installed/bundled.
- **R-33:** [Official storage/CDN host documentation](https://huggingface.co/docs/hub/datasets-downloading#downloading-behind-a-proxy-or-firewall): exact official storage hosts can change. ModelVet pins an explicit reviewed set and rejects unknown transitions; it does not adopt the vendor's wildcard suggestion or claim OS-level egress isolation.

These are vendor/source facts informing implementation. Local protocol/security tests and the public tiny-repository observation are separate engineering evidence in PROGRESS; no independent review is inferred.
