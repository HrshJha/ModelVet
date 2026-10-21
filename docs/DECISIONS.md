# Architectural decision register (ADRs)

**All entries below are `Proposed`, not previously user-approved decisions.** Date 2026-10-20. Once accepted through repository review, change status with reviewer/date. Never quietly convert a proposal into history. PRD remains authoritative for requirements.

## Index

| ADR | Topic | Status | Related FRs | Revisit |
|---|---|---|---|---|
| ADR-001 | Local-only solo-developer scope | Proposed | FR-001, FR-014 | remote requirement arises |
| ADR-002 | Python 3.12, uv, modular monolith | Proposed | FR-014, FR-015 | dependency compatibility fails |
| ADR-003 | Snapshot + SHA-256 manifest | Proposed | FR-002, FR-003 | large artifacts force reconsideration |
| ADR-004 | Typed evidence and fail-closed semantics | Proposed | FR-009–FR-013 | schema v2 needed |
| ADR-005 | Deterministic four-state policy | Proposed | FR-012 | policy scenario contradiction found |
| ADR-006 | External ModelScan subprocess | Proposed | FR-008 | upstream incompatible / residual risk too high |
| ADR-007 | TOML policy and JSON/Markdown output | Proposed | FR-013, FR-014 | user demand for alternatives |
| ADR-008 | Local declaration-only provenance/license | Proposed | FR-006, FR-007 | independent source integration justified |
| ADR-009 | No model execution in MVP | Proposed | FR-018, FR-021 | independent safety gate PH-11 passes |
| ADR-010 | Evidence-first benchmark, no USP claims | Proposed | FR-016, FR-017 | reliable head-to-head result available |
| ADR-011 | No server/database/web dashboard | Proposed | FR-014 | multi-user need demonstrated |
| ADR-012 | Report exit codes and fail-closed errors | Proposed | FR-012–FR-014 | CLI compatibility demands change |

The common ADR template is supplied for **every entry** below; implementation must record review outcome, references and replacement linkage.

## ADR-001: Local-only solo scope

- **Status:** Proposed · **Date:** 2026-10-20
- **Context:** ModelVet is documentation-only; requirement(s) FR-001/014 need a low-complexity, auditable implementation approach.
- **Problem:** Prevent incorrect security assurance or avoid needless infrastructure while preserving testability.
- **Options considered:** (1) proposed scoped design; (2) larger integrated/hosted feature; (3) postpone capability entirely.
- **Decision:** Only local bounded directories in MVP
- **Rationale:** No external services or remote trust required
- **Consequences:** Clear task interfaces and narrower supported scope; future extensions require tests and an ADR amendment.
- **Security implications:** Missing or unverifiable evidence must be explicit; changes require threat-model review, no implied immunity to malicious files.
- **Alternatives rejected:** Implicit network calls, unbounded parsing, hidden runtime execution and unconditional trust in scanner output where applicable.
- **Evidence and references:** `RESEARCH_REFERENCES.md` references R-01–R-12; project baseline in `../PRD.md`.
- **Revisit conditions:** user requires verified remote ingestion

## ADR-002: Python and modular monolith

**Provisional implementation note, 2026-10-20 (MV-001):** Python 3.12.15 and uv 0.13.3 are used on macOS arm64. uv 0.13.3 replaces the specification's 0.13.0 candidate because it is the installed Homebrew release. Runtime pins remain Typer 0.27.3/Pydantic 2.14.1. Hatchling is also in the development group so its dependency graph is locked; isolated builds constrain its transitives. `packaging` is an explicit development dependency for Python support metadata tests. Ruff is scoped to Python files to preserve prose specifications. Versions, licenses, advisory query and command evidence are in `verification/MV-001/`. This records implementation evidence; ADR status remains Proposed.

- **Status:** Proposed · **Date:** 2026-10-20
- **Context:** ModelVet is documentation-only; requirement(s) FR-014/015 need a low-complexity, auditable implementation approach.
- **Problem:** Prevent incorrect security assurance or avoid needless infrastructure while preserving testability.
- **Options considered:** (1) proposed scoped design; (2) larger integrated/hosted feature; (3) postpone capability entirely.
- **Decision:** Python 3.12, uv, standard package layers
- **Rationale:** upstream scanner compatibility, solo maintainability
- **Consequences:** Clear task interfaces and narrower supported scope; future extensions require tests and an ADR amendment.
- **Security implications:** Missing or unverifiable evidence must be explicit; changes require threat-model review, no implied immunity to malicious files.
- **Alternatives rejected:** Implicit network calls, unbounded parsing, hidden runtime execution and unconditional trust in scanner output where applicable.
- **Evidence and references:** `RESEARCH_REFERENCES.md` references R-01–R-12; project baseline in `../PRD.md`.
- **Revisit conditions:** resolved versions or platform tests fail

## ADR-003: Artifact identity and snapshot

- **Status:** Proposed · **Date:** 2026-10-20
- **Context:** ModelVet is documentation-only; requirement(s) FR-002/003 need a low-complexity, auditable implementation approach.
- **Problem:** Prevent incorrect security assurance or avoid needless infrastructure while preserving testability.
- **Options considered:** (1) proposed scoped design; (2) larger integrated/hosted feature; (3) postpone capability entirely.
- **Decision:** private bounded snapshot plus deterministic SHA-256 manifest
- **Rationale:** prevents easy TOCTOU and binds evidence to bytes
- **Consequences:** Clear task interfaces and narrower supported scope; future extensions require tests and an ADR amendment.
- **Security implications:** Missing or unverifiable evidence must be explicit; changes require threat-model review, no implied immunity to malicious files.
- **Alternatives rejected:** Implicit network calls, unbounded parsing, hidden runtime execution and unconditional trust in scanner output where applicable.
- **Evidence and references:** `RESEARCH_REFERENCES.md` references R-01–R-12; project baseline in `../PRD.md`.
- **Revisit conditions:** real model sizes exceed budget

## ADR-004: Typed evidence

- **Status:** Proposed · **Date:** 2026-10-20
- **Context:** ModelVet is documentation-only; requirement(s) FR-009/010/011/013 need a low-complexity, auditable implementation approach.
- **Problem:** Prevent incorrect security assurance or avoid needless infrastructure while preserving testability.
- **Options considered:** (1) proposed scoped design; (2) larger integrated/hosted feature; (3) postpone capability entirely.
- **Decision:** Pydantic versioned records with separate status/result
- **Rationale:** empty findings cannot be mistaken for complete coverage
- **Consequences:** Clear task interfaces and narrower supported scope; future extensions require tests and an ADR amendment.
- **Security implications:** Missing or unverifiable evidence must be explicit; changes require threat-model review, no implied immunity to malicious files.
- **Alternatives rejected:** Implicit network calls, unbounded parsing, hidden runtime execution and unconditional trust in scanner output where applicable.
- **Evidence and references:** `RESEARCH_REFERENCES.md` references R-01–R-12; project baseline in `../PRD.md`.
- **Revisit conditions:** schema upgrade needed

## ADR-005: Admission precedence

- **Status:** Proposed · **Date:** 2026-10-20
- **Context:** ModelVet is documentation-only; requirement(s) FR-012 need a low-complexity, auditable implementation approach.
- **Problem:** Prevent incorrect security assurance or avoid needless infrastructure while preserving testability.
- **Options considered:** (1) proposed scoped design; (2) larger integrated/hosted feature; (3) postpone capability entirely.
- **Decision:** substantiated BLOCK then INSUFFICIENT then CONTROLS then APPROVE
- **Rationale:** preserves independent proven policy violation without false approval
- **Consequences:** Clear task interfaces and narrower supported scope; future extensions require tests and an ADR amendment.
- **Security implications:** Missing or unverifiable evidence must be explicit; changes require threat-model review, no implied immunity to malicious files.
- **Alternatives rejected:** Implicit network calls, unbounded parsing, hidden runtime execution and unconditional trust in scanner output where applicable.
- **Evidence and references:** `RESEARCH_REFERENCES.md` references R-01–R-12; project baseline in `../PRD.md`.
- **Revisit conditions:** counterexample in policy properties

## ADR-006: Scanner adapter boundary

- **Status:** Proposed · **Date:** 2026-10-20
- **Context:** ModelVet is documentation-only; requirement(s) FR-008 need a low-complexity, auditable implementation approach.
- **Problem:** Prevent incorrect security assurance or avoid needless infrastructure while preserving testability.
- **Options considered:** (1) proposed scoped design; (2) larger integrated/hosted feature; (3) postpone capability entirely.
- **Decision:** pin and invoke ModelScan external CLI with no shell
- **Rationale:** use existing detection while isolating process contracts
- **Consequences:** Clear task interfaces and narrower supported scope; future extensions require tests and an ADR amendment.
- **Security implications:** Missing or unverifiable evidence must be explicit; changes require threat-model review, no implied immunity to malicious files.
- **Alternatives rejected:** Implicit network calls, unbounded parsing, hidden runtime execution and unconditional trust in scanner output where applicable.
- **Evidence and references:** `RESEARCH_REFERENCES.md` references R-01–R-12; project baseline in `../PRD.md`.
- **Revisit conditions:** security review requires stronger isolation

## ADR-007: TOML and report formats

- **Status:** Proposed · **Date:** 2026-10-20
- **Context:** ModelVet is documentation-only; requirement(s) FR-013/014 need a low-complexity, auditable implementation approach.
- **Problem:** Prevent incorrect security assurance or avoid needless infrastructure while preserving testability.
- **Options considered:** (1) proposed scoped design; (2) larger integrated/hosted feature; (3) postpone capability entirely.
- **Decision:** tomllib input, versioned JSON and Markdown output
- **Rationale:** dependency-minimal, auditable and human-readable
- **Consequences:** Clear task interfaces and narrower supported scope; future extensions require tests and an ADR amendment.
- **Security implications:** Missing or unverifiable evidence must be explicit; changes require threat-model review, no implied immunity to malicious files.
- **Alternatives rejected:** Implicit network calls, unbounded parsing, hidden runtime execution and unconditional trust in scanner output where applicable.
- **Evidence and references:** `RESEARCH_REFERENCES.md` references R-01–R-12; project baseline in `../PRD.md`.
- **Revisit conditions:** new interop requirement

## ADR-008: Metadata claims only

- **Status:** Proposed · **Date:** 2026-10-20
- **Context:** ModelVet is documentation-only; requirement(s) FR-006/007 need a low-complexity, auditable implementation approach.
- **Problem:** Prevent incorrect security assurance or avoid needless infrastructure while preserving testability.
- **Options considered:** (1) proposed scoped design; (2) larger integrated/hosted feature; (3) postpone capability entirely.
- **Decision:** collect local claims; never grant legal clearance
- **Rationale:** upstream license/training data lineage may be unknowable
- **Consequences:** Clear task interfaces and narrower supported scope; future extensions require tests and an ADR amendment.
- **Security implications:** Missing or unverifiable evidence must be explicit; changes require threat-model review, no implied immunity to malicious files.
- **Alternatives rejected:** Implicit network calls, unbounded parsing, hidden runtime execution and unconditional trust in scanner output where applicable.
- **Evidence and references:** `RESEARCH_REFERENCES.md` references R-01–R-12; project baseline in `../PRD.md`.
- **Revisit conditions:** reliable provenance source adopted

## ADR-009: Behavioral safety gate

- **Status:** Proposed · **Date:** 2026-10-20
- **Context:** ModelVet is documentation-only; requirement(s) FR-018/021 need a low-complexity, auditable implementation approach.
- **Problem:** Prevent incorrect security assurance or avoid needless infrastructure while preserving testability.
- **Options considered:** (1) proposed scoped design; (2) larger integrated/hosted feature; (3) postpone capability entirely.
- **Decision:** exclude model execution in MVP; P2 Linux microVM only
- **Rationale:** host-side execution is unacceptable
- **Consequences:** Clear task interfaces and narrower supported scope; future extensions require tests and an ADR amendment.
- **Security implications:** Missing or unverifiable evidence must be explicit; changes require threat-model review, no implied immunity to malicious files.
- **Alternatives rejected:** Implicit network calls, unbounded parsing, hidden runtime execution and unconditional trust in scanner output where applicable.
- **Evidence and references:** `RESEARCH_REFERENCES.md` references R-01–R-12; project baseline in `../PRD.md`.
- **Revisit conditions:** microVM adversarial safety gate passes

## ADR-010: Benchmark before superiority

- **Status:** Proposed · **Date:** 2026-10-20
- **Context:** ModelVet is documentation-only; requirement(s) FR-016/017 need a low-complexity, auditable implementation approach.
- **Problem:** Prevent incorrect security assurance or avoid needless infrastructure while preserving testability.
- **Options considered:** (1) proposed scoped design; (2) larger integrated/hosted feature; (3) postpone capability entirely.
- **Decision:** hold out fixtures; avoid unconditional USP
- **Rationale:** existing tools already handle many cases
- **Consequences:** Clear task interfaces and narrower supported scope; future extensions require tests and an ADR amendment.
- **Security implications:** Missing or unverifiable evidence must be explicit; changes require threat-model review, no implied immunity to malicious files.
- **Alternatives rejected:** Implicit network calls, unbounded parsing, hidden runtime execution and unconditional trust in scanner output where applicable.
- **Evidence and references:** `RESEARCH_REFERENCES.md` references R-01–R-12; project baseline in `../PRD.md`.
- **Revisit conditions:** independent positive result established

## ADR-011: No distributed system

- **Status:** Proposed · **Date:** 2026-10-20
- **Context:** ModelVet is documentation-only; requirement(s) FR-014 need a low-complexity, auditable implementation approach.
- **Problem:** Prevent incorrect security assurance or avoid needless infrastructure while preserving testability.
- **Options considered:** (1) proposed scoped design; (2) larger integrated/hosted feature; (3) postpone capability entirely.
- **Decision:** no server, database or UI for local CLI
- **Rationale:** cost/complexity without MVP value
- **Consequences:** Clear task interfaces and narrower supported scope; future extensions require tests and an ADR amendment.
- **Security implications:** Missing or unverifiable evidence must be explicit; changes require threat-model review, no implied immunity to malicious files.
- **Alternatives rejected:** Implicit network calls, unbounded parsing, hidden runtime execution and unconditional trust in scanner output where applicable.
- **Evidence and references:** `RESEARCH_REFERENCES.md` references R-01–R-12; project baseline in `../PRD.md`.
- **Revisit conditions:** actual collaboration need documented

## ADR-012: Exit and error semantics

- **Status:** Proposed · **Date:** 2026-10-20
- **Context:** ModelVet is documentation-only; requirement(s) FR-012/013/014 need a low-complexity, auditable implementation approach.
- **Problem:** Prevent incorrect security assurance or avoid needless infrastructure while preserving testability.
- **Options considered:** (1) proposed scoped design; (2) larger integrated/hosted feature; (3) postpone capability entirely.
- **Decision:** 0/10/20/30 decisions, 40/50 failures, 130 interrupt
- **Rationale:** clear CI integration and failure distinction
- **Consequences:** Clear task interfaces and narrower supported scope; future extensions require tests and an ADR amendment.
- **Security implications:** Missing or unverifiable evidence must be explicit; changes require threat-model review, no implied immunity to malicious files.
- **Alternatives rejected:** Implicit network calls, unbounded parsing, hidden runtime execution and unconditional trust in scanner output where applicable.
- **Evidence and references:** `RESEARCH_REFERENCES.md` references R-01–R-12; project baseline in `../PRD.md`.
- **Revisit conditions:** compatibility discussion

## MV-002 implementation note — 2026-10-20

The pinned Typer release bundles Click internally. The CLI boundary catches its `typer._click.exceptions.UsageError` and public `typer.exceptions.Abort` to translate errors to 40/130. This private exception import is covered by CLI tests and must be rechecked on Typer updates. Commands whose pipeline is absent return 50 without a decision; version advertises no report-schema support yet. ADRs remain Proposed.

## MV-003 provisional path/budget choices — 2026-10-20

Use descriptor-relative O_NOFOLLOW directory traversal on POSIX, including ancestors; unsupported secure access is rejected. Do not create output directories during validation. The proposed default resource budgets are also the initial hard ceilings, so flags can only lower them until measured review supports expansion. This implements the PRD bounds without claiming an atomic filesystem snapshot. ADRs remain Proposed.

## MV-004 conservative ingestion limits — 2026-10-20

The entry budget counts files and directories, with maximum directory depth 64 and UTF-8 relative-path length 4096 bytes. Reject non-NFC names, control characters, backslashes and case-fold collisions on both platforms to keep manifest and report path interpretation unambiguous. Cross-device traversal is rejected. Snapshot directories stay private (0700), copied files read-only (0400), and cleanup requires symlink-resistant stdlib rmtree. These are conservative scope limits; source and snapshot checks remain best-effort race detection, not atomic filesystem isolation. ADRs remain Proposed.

## MV-007 structural subset — 2026-10-20

Use bounded manual ZIP metadata reads rather than allocating stdlib ZipFile objects before checking index budgets. The initial supported subset excludes ZIP64, streaming descriptors, encryption, multidisk, alternate Unicode paths and compression other than stored/deflate; this can exclude common PyTorch checkpoints and must remain explicit UNSUPPORTED. Cap aggregate ZIP metadata at the metadata ceiling, members at the entry cap, declared expansion at byte limits, and ratio at 100. Do not validate CRC/payload or claim loader equivalence. Safetensors supports listed whole-byte dtypes; sub-byte/unknown dtypes stay unsupported. Strict JSON rejects duplicate keys, nonfinite numbers, invalid Unicode, depth over 64 and over 100,000 structural tokens. These narrower parser limits are provisional; no ADR is accepted by this note.

## MV-008–009 local declaration choices — 2026-10-20

README frontmatter supports simple scalar license/repo/revision fields only; complex YAML remains unsupported. LICENSE document titles are explicitly distinguished in source pointers from SPDX/JSON identifiers; all confidence is DECLARED. The fixed opt-in `modelvet-environment.json` envelope binds supplied environment claims to the artifact digest, avoiding implicit host package inspection or an unplanned CLI flag. Exact-version recognition is a conservative PyPI subset, not a claim about actual installed software or vulnerability reachability. No runtime dependency was added. ADRs remain Proposed.

## MV-010 external scanner environment and resource gap — 2026-10-20

Pin ModelScan 0.8.8 in an isolated eight-package environment (`tools/modelscan/requirements.lock`), separate from incompatible Rich/TOML core versions. Version and entry-point hash are observed; this does not attest the entire external environment. No h5py/TensorFlow extras are installed. Fake executable contracts and a real inert standalone-pickle scan pass. The pinned JSON includes positive named scanned files and explicit skipped files; archive member completeness still needs independent reconciliation.

On this Darwin host, RLIMIT_AS and RLIMIT_DATA reject tested limits with ValueError: current limit exceeds maximum limit. Enforce CPU, file-size, FD, output and wall-time limits; record unavailable memory caps and absent OS network isolation in every raw execution. Linux memory caps remain implemented but untested. Required scanner resource coverage must be unresolved on this macOS configuration; scanner process exit success cannot erase that gap. Subprocess execution remains conditionally trusted and is not containment. ADR status remains Proposed.

## MV-011 evidence and applicability — 2026-10-20

Export strict v1 typed evidence schema; reject status/result contradictions, unknown fields, count/identity mismatches and invented scanner paths. Pinned ModelScan named scanned-file output is positive proof only for independently classified standalone pickle-like files; archive content completeness stays inconclusive. Preserve raw hashes and REPORTED findings without automatic corroboration. Applicability version increments from 1 to 2 to add `scanner:resources`; Darwin missing memory caps produce UNSUPPORTED required resource evidence. No policy outcome may infer coverage merely from process exit. ADRs remain Proposed.

## MV-012–013 coverage and conflicts — 2026-10-20

The draft CoverageRecord omitted NOT_RUN and explicit requirement level; v1 now includes `not_run_check_ids` and `mandatory_check_ids`. Every expected pair belongs to exactly one terminal bucket. Duplicate observations are retained but cannot complete a pair. Conflict records reference claim IDs or semantic check hashes, preserve all sources, compare provenance fields independently and make license relevance policy-dependent. No automatic rights determination or signed human override is implemented. Nested JsonValue fields receive explicit finite-number/Unicode/structure validation because Pydantic config alone did not reject nested NaN in the observed test. Schemas remain draft v1; ADRs remain Proposed.

## MV-014 evaluator boundary — 2026-10-20

The proposed coverage-only evaluator signature cannot independently verify artifact binding, applicability, required claim sources or a source ban. Add required keyword inputs `classifications`, `checks`, and `claims`; recompute coverage with applicability v2 and compare supplied rows. Core identity check details must include `sha256`; classification details include `format_class` and boolean `mismatch`; source presence details include `source_present=true`. These facts must have executor `modelvet`, complete status, matching artifact digest and no error code. Corroborated repository Python presence is the only independently implemented prohibition category in v1. Scanner severity/verification labels cannot substantiate a ban; unresolved findings remain insufficient. Unknown formats, empty/model-free inventories and relevant conflicts cannot approve. An independently complete source ban may supersede unrelated missing evidence, while integrity conflicts affecting its proof prevent that ban. Control vocabulary is closed and owners are explicit; enforcement is the deployment owner's responsibility, not a host model-loading feature. Typed contracts moved into MV-014 as evaluator prerequisites; parsing remains MV-015. ADRs remain Proposed.

## MV-015 policy configuration — 2026-10-20

Use stdlib tomllib, no dependency additions, with 64 KiB/4,096-node/depth-16 limits and secure no-follow regular-file reads. Explicit policy selection replaces the embedded default; unknown fields or invalid selected files fail rather than inheriting or falling back. V1 fixes applicability at version 2 and requires an explicit mandatory/optional partition of all known check IDs; identity/classification cannot be optional. No `[limits]`, advisory/P1 fields, expressions or ambient environment policy overrides are accepted. The conservative default requires sourced LICENSE/PROVENANCE declarations and every applicable check, with a repository-code prohibition. Missing malicious-operation corroboration remains insufficient; v1 does not implement a generic scanner finding ban. Closed deployment control IDs require owners and do not provision isolation. Semantic identity ignores policy whitespace/order and binds effective rules/owners. The validation CLI is wired in MV-015 as a direct parser interface, ahead of remaining MV-018 commands. Initial parent-symlink failure now maps to InvalidInput/40. All ADRs remain Proposed; no project review is implied.

## PH-06 report/drift contract — 2026-10-20

Report v1 adds a validated reference index from semantic evidence IDs to JSON pointers so original check hashes still identify redacted records. Exact relative filenames/content identities and policy owners remain audit inputs; free text redacts host paths/common credential patterns, with original scanner bytes restricted to private raw files. Redaction is best effort, not automatic secret classification. Raw hashes/logs/environment digests and timestamps are observational; semantic projection binds normalized evidence, identity, policy, tools and decision. Output is bounded to 32 MiB and 2,000,000 JSON tokens (artifact parsers retain 100,000). A fresh 0700 run directory is reserved exclusively; private files are published using non-overwriting linkat, report.json last as completion marker. No complete JSON is left on write failure. Final source/snapshot rechecks invalidate all identity checks on drift. Doctor exit 0 signals completed diagnostics, not scan readiness; serialized readiness remains false where required memory bounds are unavailable. No dependencies added; ADRs remain Proposed.

## MV-024 security refinements

Use descriptor device/inode ancestry for output/staging/scanner containment because Path.is_relative_to alone misses case aliases on insensitive filesystems. Require unique versioned producers for complete report evidence, retain raw finding references, and reject unknown scanner exits during normalization even if a caller mislabels process success. Always terminate the launched process group on exit (no claim of containment for children that escape groups). Remote/custom loader declarations remain unresolved under static v1; no proof of loader behavior is synthesized. The policy report/reference schemas do not change shape. Initial audit assumed platform-conditional colorama was installed; it now records PyPI version metadata for absent conditional packages. All original third-party core pins match MV-001. ADRs remain Proposed.

## PH-09/10 local candidate scope

The user explicitly chose “Finish local candidate; leave hosted CI pending” after gh reported no authentication and no Linux runtime was found. CI configuration and local equivalent commands are verified; hosted success/Linux support/public release are not claimed. This scope permits local packaging/audit work while leaving release gates pending. Source archives include specs/examples/workflow and exclude operational verification records; an initial inclusion test caught a broad glob and the exclusion is now explicit. Final privacy regressions cover quoted/multiline secrets, bearer/basic authorization, access/refresh tokens and sensitive detail keys. Redaction remains best effort, preserving original source reference hashes and policy/file identity. No new third-party dependency; ADRs remain Proposed.

## MV-020 supplementary offline advisory scope — 2026-10-20

Start the next unblocked P1 task after completing the user-selected local candidate. OSV inputs use an explicit query-scoped envelope so an empty or omitted feed cannot imply universal negative evidence. Source/completeness timestamps remain unauthenticated operator declarations. Match exact enumerated PyPI versions only; unsupported ranges/conditions/ecosystems remain unresolved. No runtime dependency addition, implicit network, version-order approximation or exploitability claim. Use a separate `advisories` JSON command bound to stored report identity rather than silently changing closed policy v1/applicability v2 or promoting admission. A required workflow must combine both command exits. Explicit as-of time makes freshness reproducible. This records the narrower implementation and extension seam; ADRs remain Proposed.

## MV-022/023 development-only benchmark boundary — 2026-10-20

Closed inert recipes, generator/file/artifact hashes and alternative stdlib byte methods establish development labels; do not represent same-author method checks as independent human adjudication. The manifest rejects holdout/review promotions. The local runner preserves raw evidence, tool/repeat/identity metadata and finite budgets, excludes out-of-context/unavailable tools from paired eligibility, and distinguishes ModelScan file assessment from ModelVet admission. No reviewed discrepancy positives exist; detection/error rates and intervals remain null, with study status INCONCLUSIVE. A source-policy BLOCK is not a malicious-model false positive. Actual times are different pipeline observations, not an overhead comparison. Raw results are private and excluded from source archives; no dependency addition. User selected leaving external research/security/Linux gates pending; PH-11 review preparation is prose only. All ADRs remain Proposed.

## PH-12–14 local implementation scope

The user explicitly selected “Extend the local feature plan.” Extend static report auditing while independent review/Linux prerequisites remain pending. Add stable FR-022–024/MV-033–035 IDs and three local phases: declared raw-attachment verification, report comparison, explicit-manifest batch audit. These commands use existing reports and never call admission evaluation or model loaders. Verification means local byte/hash consistency, not author authentication or artifact safety. No dependency addition. All ADRs remain Proposed; no external gate is implicitly accepted.

## MV-026 hosted runner follow-up — 2026-10-20

GitHub access now exposes prior hosted cache failures. Prime hash-locked runtime dependencies before offline installed-package tests; do not remove offline installation/runtime guards. Ubuntu 24.04 now passes the full gate at feb9e8d. Hosted macos-15 ARM jobs remain queued; select the documented standard macos-15-intel target for the macOS hosted gate, with local arm64 evidence labeled separately. All OS checks are retained; this does not claim hosted ARM validation or dedicated Linux/KVM containment. No dependency change; ADRs remain Proposed.

## MV-011 Unicode object-key correction — 2026-10-20

The normalized JSON validator already checked string values, but direct Python construction could admit unpaired surrogates in object keys. Under the pinned serializer, a high-surrogate key became three replacement characters. Validate object keys with the same strict UTF-8 encoding used for values, at every nested object in check details and dependency advisories. Preserve valid Unicode keys and existing structural budgets. JSON input already rejected the invalid keys; no admission bypass is established. This repairs the existing v1 UTF-8 contract without a schema, policy or dependency change. ADRs remain Proposed.

## PH-15–17 workbench scope — user-authorized

The user explicitly requested implementation of the local browser workbench plan. Amend the scope of proposed ADR-001/011 for this extension: permit loopback-only FastAPI/Uvicorn, a bundled React/TypeScript/Vite interface and a private stdlib SQLite index. Core CLI dependencies stay separate through the optional ui extra. ScanService remains authoritative; worker JSON progress is observational, not evidence. UI decisions are never evaluated in JavaScript. All ADRs remain Proposed; no independent review or loader gate is accepted by this change.

## Workbench acceptance refinements — 2026-10-21

Cache capability probes before HTTP request threads start; resource-limit preexec must not run from those threads. Exclude both lexical and resolved model/workspace scanner paths, and filter worker PATH against those roots. Track launched scanner groups through bounded own-worker JSON events; POSIX parent-death polling uses a signal timer rather than a second worker thread. Recompute UI summaries from pinned, validated report bytes; index fields cannot promote admission. Bound active API requests to four and body reception to ten seconds. Job setup/thread/disk failures clean staging and cannot finalize a report. Node typings, Prettier and axe/Playwright are test/build-only tooling; axe is unmodified MPL-2.0 and is not bundled into the runtime. All ADRs remain Proposed.

## MV-043 distribution acceptance — 2026-10-21

Commit compiled frontend assets and complete upstream runtime notices so wheel/source builds do not require Node or registry access. Pin the Node CI action and runtime; rebuild and compare generated schema/types/assets in both supported CI targets. A disposable installed-wheel acceptance environment injects a trusted site-packages socket guard into the server and own worker; this is test instrumentation, not a product scanner sandbox. The application PATH contains no Node. Playwright runs separately as a test driver. Browser storage state is excluded from distributions and CI uploads. All ADRs remain Proposed.


## Mac-first product scope — maintainer direction, 2026-10-21

The maintainer explicitly instructed focusing on the Mac and changing blockers tied to unavailable platforms. Add FR-028/MV-045/PH-18 for scoped completion: the local static Mac CLI/Workbench is the deliverable; independent benchmark and Linux/KVM loader research are deferred, not product-release prerequisites. Mac preview acceptance uses internal review, bounded safe fixtures, local arm64/hosted Intel checks and installed assets. Preserve all scanner-resource/check/decision semantics and host non-execution invariants. Independent review is not claimed, and the future loader gate remains unchanged if that research is resumed. Earlier ADRs remain Proposed; this note records the explicit scope instruction without approving unrelated architecture or security claims.
