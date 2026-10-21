# ModelVet threat model — static MVP and gated future execution

**Proposed security design**, 2026-10-20. Static controls are implemented and tested; independent review is pending. PH-11 isolation remains unimplemented. ModelVet is itself exposed to attacker-controlled files and metadata. No guarantee of malicious-model detection or host safety is made.

## Trust assumptions and protected assets

**Protected:** analyst host, local accounts and credentials, other project files, subprocess environment, artifact/report integrity, accurate decision output, CI pipelines, organizational reputation from false clean reports. **Untrusted:** entire input directory, arbitrary filenames and file contents, declared source/license/revision, external scanner JSON/logs, user-controlled policy until validated, subprocess output and URLs. **Conditionally trusted:** installed scanner binary/library (verify path/version but parser vulnerabilities may exist); Python/OS runtime; P2 hypervisor and guest host configuration.

**Attacker:** can choose artifact files and archive contents, malicious metadata and unusually large structures, alter input concurrently, plant symlinks/special files, and seek a false approval or attack a scanner parser. Attacker does **not** initially control ModelVet source, pinned policy or administrator; compromised package supply chain is separate threat.

## Data/control boundaries

| Boundary | What crosses it | Main risk | Mandatory control |
|---|---|---|---|
| Local path → scanner | filenames/bytes | arbitrary read, traversal, special nodes | lstat, bounded snapshot, strict budget, no symlinks |
| Raw bytes → static parser | ZIP/safetensors/JSON metadata | parser bugs, bombs, metadata spoofing | bounded reads, safe parsing, duplication rejection, fuzz/property tests |
| Snapshot → external ModelScan | untrusted artifact | parser exploitation, process escape, hang | no shell, sanitized env, timeouts, memory/CPU/file limits; not a full sandbox |
| Scanner result → normalizer | stdout/file/JSON | false-clean, skipped records, forged IDs | schema validation, independent artifact IDs, refuse ambiguous coverage |
| Evidence → policy | normalized findings/statuses | rule bypass, missing evidence promoted | typed predicate, precedence, conflict handling, deterministic tests |
| Report writer → filesystem | paths/logs/raw findings | overwrite, disclosure, tamper | output outside input, mkdir 0700, create 0600, atomic replace, no secrets |
| URL argument → Hub reference parser (proposed) | user-controlled URL | parser confusion, arbitrary endpoint, credential leakage | exact HTTPS host/path grammar; reject user-info, query/fragment, ports, encodings and unsupported routes |
| ModelVet → Hub metadata/download (proposed) | request, optional token, remote metadata/bytes | SSRF, redirects, DNS rebinding, malicious metadata, token exfiltration, DoS | fixed official endpoint; per-hop host/IP checks; bounded inventory/streaming; read-only token; never serialize token; block fetch feature if client controls are inadequate |
| Hub inventory → local snapshot (proposed) | remote path, size, blob/LFS/Xet identifiers | traversal, case/Unicode collision, wrong bytes, partial/cache poisoning | canonical relative-path validation, descriptor/no-follow staging, pinned commit, local SHA-256, rehash cache hits, incomplete coverage on any mismatch |
| P2 artifact → microVM guest | model loader and runtime | guest code execution, VM escape, data exfiltration | dedicated host, KVM, jailer, seccomp, no host secrets/network, disposable guest; independent review |

## Threat register and detection limits

| ID | Scenario | Attack surface / impact | Intended mitigation | Detection scope / residual risk | Tests |
|---|---|---|---|---|---|
| TM-01 | Embedded pickle gadget | `pickle`, `.pt` | never unpickle on host; existing scanner adapter | known gadgets might be detected; evasion remains | T-SCAN-01, T-BENCH-01 |
| TM-02 | Malformed ZIP / iteration abort | `.pt` / archives | independent index count, capture errors, require covered entries | loader-specific semantics not proved by index alone | T-STRUCT-01, T-COV-01 |
| TM-03 | Path traversal or ZIP slip | archive names | index-only no extraction; reject unsafe member paths | nested parsing can still have bugs | T-STRUCT-01 |
| TM-04 | Decompression/metadata bomb | archive headers | cap entries, declared sizes, metadata and ratios; no unzip | metadata may lie | T-STRUCT-01 |
| TM-05 | Symlink/hardlink/special input | filesystem | lstat reject symlinks/devices/FIFO, bound root; snapshot | filesystem races are not eliminated completely | T-INV-01 |
| TM-06 | Source mutation during scan | active directory | private snapshot, original rehash | cannot guarantee atomic consistent external FS snapshot | T-REPRO-01 |
| TM-07 | Python repo code auto-import | `modeling_*.py` | never run `from_pretrained` or import source; explicit policy class | missed executable path in config | T-CLASS-01 |
| TM-08 | Unsafe loading flag | config/loader metadata | detect declared `trust_remote_code` and expose risk | static evidence may not describe actual invocation | T-META-01 |
| TM-09 | Unknown/unsupported format | custom binary | explicit UNSUPPORTED required check | format recognition error | T-CLASS-01, T-COV-01 |
| TM-10 | Tool crash/timeout | subprocess | bounded timeout, status FAILED, fail closed | crash due to code exploit remains possible | T-SCAN-01 |
| TM-11 | Scanner reports false clean | raw JSON | separate status/result, per-file proof, independent coverage expectations | unknown scanner behaviors; no perfect detector | T-COV-01 |
| TM-12 | Version/advisory mismatch | environment manifest | pinned versions and time-stamped offline advisory feed | known CVE not necessarily reachable; stale feed | T-OSV-01 |
| TM-13 | Incorrect license claim | README/config | record source and conflict, no legal verdict | training-data lineage unknown | T-META-01, T-CONFLICT-01 |
| TM-14 | Report/metadata tamper | JSON output | immutable hashes, restricted directory and schema | user with output permissions can still alter file | T-REPORT-01 |
| TM-15 | Dependency confusion | package install | locked deps, trusted sources, review | compromised registry/package still possible | T-RELEASE-01 |
| TM-16 | Sensitive path/token exposure | scanner stdout/env | sanitized env, redact paths, limit stderr | malicious scanner can read files if OS permits | T-REPORT-01 |
| TM-17 | Policy manipulation | TOML config | explicit policy hash, schema, no implicit env overrides | malicious authorized policy operator out of scope | T-POLICY-01 |
| TM-18 | P2 VM escape / egress | dynamic loader | dedicated patched hypervisor, no net/secrets, monitored boundary | zero escape-risk impossible | T-VM-01 |
| TM-19 | Hidden triggers not exercised | P2 behavioral | bounded test coverage / unknown status | absence of observation ≠ proof of safety | T-VERSION-01 |
| TM-20 | Host memory exhaustion | scanner or ingestion | total/file bytes/time limits; process limits; no GPU load | OS resource attacks may bypass weak process controls | T-RESOURCE-01 |
| TM-21 | SSRF or internal-network fetch | URL/network client | exact URL grammar; fixed endpoint; validate every redirect and resolved address; deny private/reserved/loopback/link-local targets | DNS/rebinding and client internals require version-pinned adversarial tests; if unenforceable, do not ship remote fetch | T-HF-URL-01, T-HF-NET-01 |
| TM-22 | Malicious redirect or cross-origin token leak | HTTP redirects/auth | explicit approved host set; prohibit credential forwarding across origins; TLS only; inspect every hop | Hub storage host list may evolve and needs source review on client upgrades | T-HF-NET-01 |
| TM-23 | Malicious repository paths/metadata | Hub API response | bound metadata bytes/count/path length; reject traversal, ambiguity, duplicate normalized names and non-file rows | upstream metadata is not an integrity guarantee | T-HF-INV-01 |
| TM-24 | Oversized/excessive downloads or retries | file transfer | advertised and streamed byte caps, wall time, one concurrent download, bounded transient retry, no decompression | remote size can be absent or wrong; streamed cap is authoritative | T-HF-FETCH-01, T-HF-RESOURCE-01 |
| TM-25 | Wrong revision/content or mid-run change | moving refs, transfers, cache | resolve full commit once; list and fetch only at it; local hash; compare verified upstream digest when available; no silent fallback | Git/LFS/Xet identifiers have different semantics; report source and hash limits | T-HF-INV-01, T-HF-INTEGRITY-01 |
| TM-26 | Secret exposure | local Hub token, env, errors, reports | explicit local credential selection; read scope; no token in URL/argv/output/report; redaction tests | dependencies/process crash dumps may retain transient memory; local account compromise out of scope | T-HF-AUTH-01 |
| TM-27 | Partial transfer or disk exhaustion | staging/cache | private unique temp, streamed digest, atomic complete promotion, cleanup, report unresolved state; cache disabled initially | cleanup can be interrupted by power loss; later startup cleanup must be owner-only and bounded | T-HF-FETCH-01, T-HF-RESOURCE-01 |

## Static safety baseline

1. **Inspect as data only:** use `hashlib`, `zipfile` index and bounded `struct/json`, never `pickle.load`, `torch.load`, `joblib.load`, `dill.load`, `eval`, `exec`, `importlib` on downloaded repository modules or Transformers `from_pretrained` on the ordinary host.
2. **Path handling:** validate canonical relative paths, reject symlinks/mount surprises and special files; inspect `lstat` metadata, avoid `follow_symlinks=True`; use secure temp dir + ownership restrictions; reject output path under input root. Hardlinks not reliably identified with path checks alone: record link count and reject hardlinks with `st_nlink > 1` for MVP or copy+rehash with explicit limitation.
3. **Resource ceilings:** proposed 10k files, 1 GiB/file, 2 GiB total, 16 MiB per metadata read, scanner 120s; exact ceilings to verify experimentally. Input over budget errors without approval. ZIP/member count, duplicate names, paths and ratios require separate caps.
4. **Subprocess:** executable allowlist and exact version verification, `subprocess` argv array, `shell=False`, `close_fds=True`, environment allowlist without tokens, owner-only temp cwd, timeout and `kill` process group, ulimits/platform controls where available; record if limits cannot be enforced. **Not** a safe sandbox for an exploitable scanner parser.
5. **Network:** disabled for ModelVet MVP; subprocess env proxy credentials removed; OS network prohibition for scanner process needs platform test. No absolute "offline scanner" guarantee until tested.
6. **Failures:** scanner crash/skip/no-supported/unknown JSON yields status `FAILED/UNSUPPORTED/INCONCLUSIVE`; if check mandatory then decision INSUFFICIENT unless independent rule justifies BLOCK. Do not manufacture an empty-success record.
7. **Result integrity:** rehash frozen files, compare manifest; raw results hashed and retained only within configured bound; semantic digest binds all check states and policy.

## P2 microVM prerequisite threat gate (not implemented)

- **Authorization:** opt-in command only after review and code audit; cannot be called implicitly from `scan`.
- **Host:** dedicated Linux KVM-capable test machine, patched kernel/microcode/hypervisor and guest, non-root jailer UID/GID, seccomp and cgroup restrictions per Firecracker guidance, no host user data/credentials in guest, no ambient AWS/GCP keys, no host writable mounts, network disconnected. Guest image fixed/hash pinned, no arbitrary caller-supplied kernel/init scripts.
- **Execution scope:** only synthetic/authorized controlled artifacts at first; capture PID/network/file events; bound memory/CPU/process/seconds; save event traces outside VM via controlled channel.
- **Failure behavior:** sandbox unavailability, instrumentation gap, timeout, escape warning or identity drift → `INCONCLUSIVE`; nothing yields blanket safe status.
- **Approval required:** human review of isolation config, independent negative tests, CVE patch inventory, confirmed teardown, only then enable experimental API.

## Security claims allowed / forbidden

Allowed: "The configured checks completed on artifact digest X and policy version Y"; "ModelScan reported findings/was skipped"; "A controlled load attempt in guest Z observed action A." Forbidden: "malware-free," "safe to load everywhere," "licensed for all commercial uses," "no zero days," "100% detection," "VM is perfectly secure," or "we found a new vulnerability" without independent verification.

## Residual risk register

Even a clean static assessment cannot rule out malicious payloads, untested native loaders, learned backdoors, delayed behavior, scanner parser exploitation, repository metadata deception, CVEs absent from snapshots, filesystem races or VM escape. Public-facing reports must repeat scope and limitations; a policy APPROVE is conditional on exact inputs and does not substitute for standard isolation in production workloads.

## MV-020 advisory boundary

Optional local snapshots are untrusted, bounded data. Refuse linked/special/oversized/changing files, duplicate query/record identities and malformed timestamp/schema/JSON. Require exact query scope and explicit completeness; stale/missing/partial/unsupported data cannot complete a required supplement. Snapshot SHA-256 and report/artifact IDs bind provenance, not publisher authenticity. A malicious operator can still supply false timestamps/completeness; no signature verification or online freshness guarantee is claimed. Range semantics and actual package installation/reachability are unverified. Supplementary evidence never changes a stored admission decision; required workflows must enforce both scan and advisory exits.

## MV-022/023 development experiment boundary

Only closed inert recipes are generated: bounded malformed/index/declaration cases and a strict static pickle opcode allowlist. No archive extraction or model loading occurs on the host. The manifest cannot select an executable, external payload, arbitrary path, hidden split or independent-review status. Generator/file/artifact identities and an alternative static method must agree. Existing ModelScan process boundaries apply; raw output remains private and untrusted. Corpus labels and pilot metrics do not establish exploitability or loader behavior. No review or host gate is relaxed by development repeat agreement. The PH-11 proposed review packet is preparation only and enables no runner.

## Stored report audits — FR-022–024

Stored reports, batch manifests and raw attachment paths remain untrusted. Audit reads reject linked/special files and unsafe ancestry; canonical relative manifest paths cannot select outside the explicit root. Raw filenames are constructed only from validated SHA-256 values. Count, per-file and shared byte ceilings bound work; report/manifest/root rechecks detect observed changes. These checks are best effort, not an atomic snapshot against a concurrent attacker.

A consistent report plus raw bytes is forgeable by its author. VERIFIED authenticates neither author nor model safety; an external hash pin only checks equality to the operator-supplied pin. No failed/unprocessed batch row can produce aggregate VERIFIED, and no audit promotes admission. Comparison hides free text and relative paths by default; hashes remain linkable. Stdout redirection permissions belong to the caller (`umask 077` examples). No network, deserialization, artifact import or new dependency is introduced.

## Workbench extension — FR-025–027

The optional loopback HTTP interface is a new trust boundary. Require launch-token exchange, authenticated reads, CSRF on mutations, exact Host/Origin validation, no cross-origin sharing, strict body limits, CSP and no telemetry/CDNs. Browser paths are relative to one explicitly selected root, with descriptor/no-follow containment and root identity rechecks. Workspace, policies, job descriptors and index are owner-only; reports remain outside model inputs. Workers receive fixed own-module argv and private JSON descriptors, not shell commands or arbitrary modules. Cancellation must clean scanner process groups and snapshots. History/imported reports are untrusted; schema validation and byte pins apply on every use. This boundary is not a sandbox or a loader implementation.


## Mac-first product boundary — FR-028

The maintainer narrowed the current deliverable to the available Mac. Independent benchmark and Linux/KVM loader experiments are deferred rather than current release prerequisites. This narrows product scope without changing host non-execution, strict path/body/byte limits, mandatory coverage, report privacy, scanner risk or fail-closed admission. Darwin missing memory-bound evidence stays UNSUPPORTED; no default policy check becomes optional. The Linux/KVM isolation gate above still applies if loader research is ever resumed. Internal Mac preview review must not be described as independent security certification.

## Proposed local Hub retrieval boundary — FR-029–034

Hub network traffic is opt-in by choosing a repository URL; the existing local-directory workflow remains available. A local CLI can still reach internal services, so “not a web service” is not an SSRF mitigation. The URL parser emits only canonical `repo_id` plus revision; user-provided host, proxy and endpoint values never reach a generic request API. Fix the client endpoint, inspect and constrain every redirect and resolved address, and strip credentials on cross-origin transitions. Audit client-controlled DNS/redirect behavior on every pinned-client upgrade. If the official client cannot expose enough controls, implementation must stop or use an independently reviewed transport adapter; convenience is not a reason to weaken the network boundary.

Treat all API fields as hostile. Bound pagination, response size, file count, path bytes and elapsed time. Validate repository-relative paths before local staging. Never decompress/download an archive wholesale to assess its members; use existing bounded inspection. Resolve a full commit before inventory; retrieve only explicit paths at that commit, stream through byte caps into private staging, hash locally, and discard incomplete files. Hub-provided size/blob/LFS/Xet IDs are source claims; preserve them with source labels and do not conflate them with ModelVet SHA-256. Cache is disabled initially. Public repositories need no credential; private/gated retrieval only uses the user's explicitly chosen local token or `HF_TOKEN`, read access, and individual Hub authorization. Report token presence only as configured/not configured. No token appears in command-line arguments, logs, exception messages, reports or digest. See [HUB_ASSESSMENT_SPEC](HUB_ASSESSMENT_SPEC.md) for provisional resource defaults, failures and tests.

## Implemented Hub candidate boundary — 2026-10-21

The proposed controls above now have local engineering implementations/tests in hub/reference.py, transport.py, client.py, retrieval.py and assessment.py. The official client 2.2.0 source was reviewed; the direct stdlib transport avoids its auto-redirect/Xet/cache stack. Exact storage hosts, public-address validation, pinned numeric socket connections and original-host TLS verification, permanent credential stripping after cross-origin redirects, bounded metadata/streaming, no automatic retries and a 600-second assessment timer are enforced. Explicit HF_TOKEN is the only initial credential source; no token is gathered or persisted. Workbench networking is confined to the existing own-module worker after an authenticated URL submission. No model loading occurs. Report v2 preserves retrieval omissions and rejects incomplete-source approval; local v1 checks/policy remain authoritative. This is not independent certification or proof against OS/TLS/scanner vulnerabilities. The detailed implemented contract and residual limits are in HUB_ASSESSMENT_SPEC; a future public release/host-list upgrade needs its own review.
