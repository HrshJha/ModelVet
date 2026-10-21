# Instructions for coding agents

**Mandatory reading order:** `PRD.md` → `docs/DECISIONS.md` → `docs/THREAT_MODEL.md` → `docs/ARCHITECTURE.md` → the one selected task in `docs/TASKS.md` → corresponding interface/test specs. Implementation state is recorded in `docs/PROGRESS.md`. Inspect actual files; do not infer that planned paths or commands exist.

## Operating loop

1. Inspect the actual root (`pwd`, `git status --short`, `find . -maxdepth 3 -type f`), identify user changes, and preserve them.
2. Find the **first unblocked, incomplete P0** `MV-###` task in roadmap phase order (PH-01 through PH-07, then PH-09/10). Do not let optional P1 work delay the P0 release gate. Initially **MV-001**.
3. Read its `FR-###`, expected files, prerequisites, failure modes, test names and exit criteria.
4. Implement **one coherent task** without speculative adjacent work. Keep `core`, `inventory`, `evidence`, `coverage`, `scanners`, `policies`, `reports` boundaries separate. No model deserialization anywhere in host code.
5. Add unit/integration tests for clean, malformed, missing, conflicting, unsupported and error paths relevant to the change.
6. Run the exact task command once the manifest exists; run broader checks when available. Preserve actual terminal output or log references. Never label commands VERIFIED without successful execution.
7. Inspect the diff and dependency lock changes; update `DECISIONS.md` for design deviations, `PROGRESS.md` with verifiable results, and task status only if DoD is met.
8. Report change, tests executed, security impact, remaining limitations and next unblocked task. Never claim the entire repository is finished after a single task.

**Next-version scope note (2026-10-21):** The published `v0.1.0-mac-preview.1` is local-directory-only. The maintainer has proposed Hugging Face model-repository URLs as the primary input for a future local CLI release, keeping local paths supported. This is documented as FR-029–034 / PH-19–20 / MV-046–053 and is not implemented. Since all prior P0 tasks are complete for the published scope, select MV-046 as the first unblocked task for this proposed feature; do not restart completed tasks. Follow `docs/HUB_ASSESSMENT_SPEC.md` and resolve OQ-15 before any content-fetch implementation.

## Security invariants (cannot be relaxed casually)

- Treat user paths, all artifact bytes, repository metadata, license claims, and scanner JSON as **untrusted**.
- Never invoke `pickle.load`, `torch.load`, `from_pretrained`, `eval`, `exec`, import arbitrary repository `.py`, or run untrusted model code inside the ordinary host process.
- Scanner subprocess calls must use `shell=False`, bounded wall time/resources, fixed argument arrays, sanitized environment and explicit output size limits. A subprocess is **not** a sandbox.
- Reject symlinks/special files, path traversal, unsafe output paths, oversized inputs, and scan-time identity drift without silently continuing.
- Required missing/failed/skipped/unsupported checks yield `INSUFFICIENT`, except a separately substantiated explicit policy prohibition may yield `BLOCK`.
- Preserve raw scanner evidence and normalized evidence; never conflate scanner exit code with final admission decision.
- Never use an LLM for the deterministic admission engine.
- No behavior sandbox until PH-11 security gate, isolation threat review and controlled fixtures are satisfied.
- Remote Hub input is not generic URL fetching. Validate exact HTTPS Hugging Face model URLs; resolve immutable revision; inventory before fetching; retrieve explicit files only within hard caps; validate every redirect/address; hash local bytes; keep every omission in coverage. If the pinned client cannot enforce endpoint/redirect/IP/byte/time controls, stop the remote-fetch task rather than relaxing controls.
- Never search, enumerate, create, request the user to paste, or reveal API keys/tokens. Public Hugging Face repositories need no token. Private/gated access may use only an explicitly selected user-owned local credential or `HF_TOKEN`; do not serialize or log it, put it in a URL/argv, or send it anywhere beyond the official Hub auth request.

## Change protocol

- PRD controls *what*; proposed ADRs become Accepted only after explicit project review, not just because an agent wrote them.
- Add a new FR or task with a new stable ID; do not renumber. Update PRD traceability, ROADMAP and TASKS together.
- Every dependency addition requires stack rationale, license check, lock update, and security review.
- Every new scanner adapter must pass an adapter contract suite: exit statuses, malformed JSON, skipped files, version and timeouts.
- Reports containing paths and metadata may be sensitive; protect temp files, avoid logging credentials, and do not commit hostile fixtures or operational secrets.
- Cite primary evidence in RESEARCH_REFERENCES, distinguishing vendor claims from independent tests.
- For blockers, document exact failure and feasible scope reduction; never claim benchmarks, superiority or tests that did not run.
