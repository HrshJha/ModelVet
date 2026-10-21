# Hugging Face repository assessment — local candidate

**Status:** implemented in the working tree, 2026-10-21; not included in the published `v0.1.0-mac-preview.1`. FR-029–034 / MV-046–053 cover the URL workflow. The maintainer explicitly requested the Workbench URL form as well as CLI support. Local folders remain supported. Independent benchmark and loader research remain deferred.

## User workflow and interfaces

In Workbench, choose **New scan → Hugging Face URL**, paste `https://huggingface.co/owner/model`, optionally specify a revision, review limits and start. The URL source is the default; **Local folder** retains the rooted picker. Public repositories require no API key. The browser never fetches Hub content itself: the authenticated API starts the existing dedicated worker, which performs retrieval and calls `ScanService`. Actual inventory/retrieval stages precede the existing scan stages. Cancellation and restart retain the established job semantics.

```sh
modelvet scan https://huggingface.co/owner/model --revision COMMIT_OR_REF --out /safe/reports
modelvet scan /local/model --out /safe/reports
```

POST `/api/v1/scans` accepts exactly one nonempty `model_path` or `hub_url`, optional `revision`, and `use_hf_token=false`. Policy/scanner/resource fields retain their existing meanings. The generated OpenAPI/TypeScript contracts describe the addition. Report summaries include a small `hub_source` projection; complete inventory is paged/searchable at `/api/v1/reports/{id}/evidence/retrieval`. JSON/Markdown exports include complete source records. Imports, comparisons and attachment verification accept current v1 and v2 reports without recomputing admission.

## Reference and credential boundary

Only HTTPS on exact `huggingface.co` is accepted, preserving owner/model spelling and normalizing host case. Support one optional trailing slash and `/tree/REV` with one unencoded revision component. A separately selected revision may contain canonical slash-separated components; conflicting embedded/selected revisions fail. Reject Dataset/Space/API/resolve/raw routes, extra routes, user-info, ports, percent encoding, queries (including an empty `?`), fragments, backslashes, controls, ambiguous path components and invalid repo/revision names. Errors never echo an input that might contain credentials.

Public mode never reads saved tokens. For private/gated access, the operator configures a read-only/fine-grained **HF_TOKEN** before launching the CLI/server and explicitly chooses `--use-hf-token` or the Workbench checkbox. This implementation deliberately supports only that environment source, with no saved-credential lookup/login/account fallback. Workbench reports only configured/not configured. Tokens never enter URL, argv, descriptor, index, report, digest, event or log. The worker receives HF_TOKEN only after explicit selection; the existing scanner environment excludes it. ModelVet cannot establish token scope locally; the operator must supply a suitable read token and have repository authorization.

## REST transport decision and controls

Reviewed official `huggingface_hub` **2.2.0** source: its default HTTP client follows redirects, and file downloads may delegate to the separate native Xet stack and cache. Those default paths do not implement ModelVet's connection-level DNS pinning and streamed byte contract. Use a narrow **stdlib HTTPS transport** against the documented REST API instead; no third-party client, Xet runtime, HTTP dependency or new lock entries are added. This is a recorded design deviation, with local engineering review and adversarial tests; independent certification is not claimed.

Transport version is `modelvet-https/1`. It ignores proxy/endpoint environment overrides, cookies and cache. Every request/redirect requires HTTPS/443 and an exact reviewed hostname. Current allowlist: `huggingface.co`, `cdn-lfs.huggingface.co`, `cdn-lfs-us-1.hf.co`, `cdn-lfs-eu-1.hf.co`, `cas-bridge.xethub.hf.co`, `cas-bridge.xethub-eu.hf.co`, `us.aws.cdn.hf.co`, `us.gcp.cdn.hf.co`, `transfer.xethub.hf.co`, `transfer.xethub-eu.hf.co`. Host-list changes require source review; there is no suffix wildcard or runtime extension from remote metadata.

DNS answers are bounded and checked as public unicast addresses, excluding private/reserved/loopback/link-local/site-local/multicast and mapped IPv4. Connect directly to a validated numeric address, retain the original TLS verification hostname/SNI, and verify the connected peer. Each redirect repeats those checks. Authorization is sent only to the Hub origin and is permanently stripped for that request chain after a cross-origin transition. Limit redirects to six requests, require identity HTTP encoding, and never decompress a downloaded archive or HTTP body. DNS resolution has a five-second wait; the dedicated resolver exits before scanner launch on success. A failed request stops subsequent network transfers. No automatic retry is performed; the operator can explicitly rerun.

## Inventory, retrieval and integrity

Resolve model info to a full 40-hex commit before listing the recursive tree at that commit. A supplied full commit must match the returned commit. Pagination may continue only the exact pinned tree endpoint; loops, malformed metadata, ambiguous paths, count/byte caps and inconsistent upstream IDs fail. Tree directory rows are validated; only file rows produce scan candidates. Reject traversal, links/non-file types, case-fold/Unicode collisions, conflicting file ancestors and malformed size/hash records. No download or account fallback to `main` occurs.

Identity/classification are mandatory for every file, so the explicit selection includes every inventoried file that fits the selected ceilings, in stable order. One transfer runs at a time. Oversized, over-budget and failed rows stay in the source inventory, with required check IDs and controlled reasons. No placeholder file or invented hash represents omitted content. Filename-based check requirements for omitted content are conservative; final signature-based applicability is established only on retrieved bytes.

Create private temporary directories/files through no-follow descriptor-relative writes. Stream through advertised/per-file/remaining budgets, hash locally, require the exact inventory size, check a returned commit header when supplied, compare documented LFS SHA-256 or native Git blob SHA-1 (`blob <size>\0<bytes>`), fsync and atomically publish only complete files. Native Git SHA-1 is an upstream consistency check, not a security attestation. Local SHA-256 binds every assessed file. A free-space preflight reserves capacity for downloaded bytes plus the scan snapshot and report allowance; storage races/failures still fail closed. Partial files are removed on transfer/storage/integrity failure or cancellation. Cache is disabled. The existing snapshot and final identity checks run after retrieval; source binding rejects changed bytes.

| Resource | Implemented default / ceiling |
|---|---|
| Inventory entries (including directories) | 10,000; maximum 100 pages |
| Metadata response bodies combined | 16 MiB; bounded strict JSON parsing |
| Canonical remote file path | 1,024 UTF-8 bytes / 32 components |
| CLI file / aggregate transfer | 1 GiB / 2 GiB hard ceilings; may be lowered |
| Workbench Hub file / aggregate defaults | 64 MiB / 128 MiB; user may raise only within hard ceilings |
| Whole assessment | 600 seconds, checked by process signal and Workbench supervisor |
| Socket I/O idle / connection timeout | up to 20 seconds, tightened by remaining assessment deadline |
| DNS / redirects / retries / concurrency | 5 seconds / 6 requests / 0 automatic / 1 |

These are bounded engineering settings, not throughput promises for large models. Files over the caps remain unresolved. CLI and Workbench may return no completed report for metadata/access/deadline failure; no success is inferred. Transfer failures that can be represented produce a partial evidence report.

## Coverage and report compatibility

The static classifier, inspectors, ModelScan adapter, local declarations, evidence normalization and policy remain authoritative. Do not load repository code, deserialize weights or substitute Hub safety badges for a check. Download completion is separate from assessment coverage. Retrieved files use the existing per-file check matrix. Every omitted path retains prospective mandatory pairs in the source inventory, all unassessed. Repository completeness is an additional admission prerequisite: incomplete retrieval forces `INSUFFICIENT` using `INVALID-EVIDENCE`, while a separately substantiated existing policy `BLOCK` is preserved. No missing byte can yield `APPROVE` or `CONTROLS`.

Local reports still serialize as **1.0.0**, without a `source` key and with their original semantic projection. Remote reports use **2.0.0**, requiring `source` with canonical URL/repo, requested revision, pinned commit, metadata response digest, transport version, limits and complete ordered file inventory. Rows retain advertised size, upstream blob/LFS IDs, retrieval status/reason, local SHA-256 only after complete retrieval and required check IDs. Retrieved rows must exactly match report file size/hashes and policy applicability. Missing/inconsistent source binding is rejected during report parsing. Published old v1-only readers reject v2; upgrade the reader rather than strip the source. `report-v1.json` is retained; `report-v2.json` describes the current compatible reader.

V2 semantic identity binds schema, canonical repository/commit, inventory, retrieval outcomes/local hashes, limits, normalized evidence, tools, policy and decision, using a v2 digest domain. Run time/ID and raw metadata-response digest are observational, excluded from semantic identity. This avoids moving download counters changing the semantic result for the same frozen evidence. A digest does not authenticate upstream metadata, publisher or safety. Existing raw scanner attachments retain their ordinary private-file contract.

## Acceptance and traceability

| Requirement/task | Contract IDs | Implemented tests |
|---|---|---|
| FR-029 / MV-046 | T-HF-URL-01, T-HF-AUTH-01 | `tests/test_hub_reference.py`, `tests/test_workbench_hub.py` |
| FR-030 / MV-047 | T-HF-INV-01 | `tests/test_hub_inventory.py` |
| FR-031 / MV-048 | T-HF-FETCH-01, T-HF-RESOURCE-01, T-HF-NET-01 | `tests/test_hub_retrieval.py`, `tests/test_hub_transport.py` |
| FR-032 / MV-049 | T-HF-INTEGRITY-01 | `tests/test_hub_retrieval.py`, `tests/test_hub_report.py` |
| FR-033 / MV-050–051 | T-HF-COV-01, T-HF-CLI-01 | `tests/test_hub_coverage.py`, `tests/test_cli_hub_scan.py`, `tests/test_workbench_hub.py` |
| FR-034 / MV-052–053 | T-HF-REPORT-01, T-HF-E2E-01, T-HF-SEC-01 | `tests/test_hub_report.py`, `frontend/tests/workbench.spec.ts`, full installed-package gate |

Routine tests use inert protocol doubles and synthetic static data, without live credentials or large downloads. A separately observed live public `hf-internal-testing/tiny-random-bert` run pinned commit `f171d7baecaf37b5da5a3616d8833b9969753535`, retrieved 9 files under 1 MiB/file and 2 MiB total, retained the oversized tenth file and emitted schema-valid `INSUFFICIENT` JSON/Markdown. Actual final commands/results are recorded in PROGRESS; live availability, general Hub compatibility, hosted CI, independent review and publication are separate claims.
