# ModelVet Workbench v1 — FR-025–027

User-authorized PH-15–17 extension. Local static review only; admission semantics and report v1 are unchanged. All ADRs remain Proposed.

## Launch and storage

`modelvet ui --models-root DIR [--workspace DIR] [--port 0] [--no-browser]` serves only 127.0.0.1. Default workspace is ~/.local/state/modelvet/workbench, outside the model root. Its owner-only index, lock, policies, tasks and reports persist. One process owns a workspace; one scan runs at a time. No automatic retention deletion.

React/TypeScript/Vite assets are built into the Python distribution. FastAPI/Uvicorn are optional ui dependencies; ordinary CLI imports require neither. Node is build/test-only. No remote fonts, scripts, telemetry, model upload/download, native model loading or account service.

## Session and request boundary

A cryptographically random single-use launch token crosses in the browser URL fragment. The frontend immediately removes the fragment and exchanges it at POST /api/v1/session for an HttpOnly SameSite=Strict session cookie and a CSRF token held in memory. Refresh recovers the CSRF token through the authenticated session GET. All API reads require authentication, except initial session creation. Every mutation requires exact Origin, JSON content type and CSRF (session creation uses the launch token). Exact numeric-loopback Host including port is required. No CORS, proxy trust or external assets. HTML receives CSP, frame denial, nosniff and no-referrer; APIs are no-store. Tokens never appear in access logs, report data or persisted index.

Body ceilings: 64 KiB configuration/policy, 32 MiB report import. Stream/count bodies before parsing, including chunked bodies; reject malformed/duplicate/nonfinite JSON. Return controlled 400/401/403/404/409/413/422/500 errors without raw paths, artifact text or stack traces.

## API and jobs

- Session create/read; capabilities; rooted directory listing (relative path only, bounded/paged).
- Policy validate/import; scan create/status/cancel. Request contains relative model path, selected policy ID, scanner choice and limits bounded by the existing ceilings. No scanner executable or output path can be supplied over HTTP.
- Report list/summary and paged files/checks/findings/claims/conflicts/coverage; import/download; attachment verification and two-report comparison. IDs are opaque; paths are resolved only from validated workspace records. JSON download preserves original bytes. Markdown is escaped through the existing renderer.
- Jobs keep independent `running`, `cancelling`, `completed`, `cancelled`, `failed`, `interrupted` lifecycle, actual stage, elapsed time, controlled error and optional report ID. A completed job may have any admission state. Poll at one second while active. Progress is observational and never enters evidence/digests.
- Worker uses a fixed own-module executable and private JSON descriptor. Its stdout is a bounded JSON-line protocol (no arbitrary log streaming). Cancellation interrupts the worker so existing scanner-group cleanup and snapshot finally blocks execute. Stop accepting new jobs on shutdown and wait for cleanup. Restart never automatically reruns unfinished jobs. Final report validation and a recorded byte pin precede indexing; report bytes are revalidated on use.

## UX and acceptance

Dark charcoal/cyan developer interface, system sans/monospace fonts, text/icon status labels, keyboard focus and reduced-motion support. Setup → real scan → decision/reasons → coverage/evidence → deterministic advice → compare. Guidance cites existing check/rule IDs and never edits artifacts. Stored reports are assertions, not authenticated safety certificates. Imported JSON with missing declared raw attachments cannot verify those bytes. Demonstrations are explicitly labeled and excluded from real history.

Test clean/malformed/missing/conflicting/unsupported data, all decisions, CLI parity, token replay/CSRF/host/origin/path attacks, symlink/hardlink/special files, model/workspace overlap, cancellation/cleanup/restart, disk failures, report tampering/XSS, responsive 375/768/1024/1440 layouts and installed-package operation without Node/external network. Actual evidence goes in verification/workbench; publication still requires independent review.
