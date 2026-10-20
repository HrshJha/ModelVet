# ModelVet security handling and disclosure policy (proposed)

Status: draft guidance for open-source repository maintainers; no software release exists. Applies to implementation and documentation contributions.

## Security defaults

- ModelVet processes only local directories in MVP and does not download or execute unknown model code.
- Limit input size/files/metadata, reject symlinks/special files/path traversal and disallow report paths inside input.
- External scanner invocation: fixed argv (`shell=False`), sanitized environment, bounded time/resources, no shell expansion. Treat scanner process as potentially vulnerable, **not isolated by merely being a subprocess**.
- If required evidence is missing, unsupported, failed or inconclusive, return `INSUFFICIENT`; allow `BLOCK` only for independently substantiated explicit prohibition. Do not imply `APPROVE` certifies model safety.
- Test only safe fixtures in ordinary CI. Potentially malicious real samples belong in a separately approved environment, not the default repo or pytest collection.

## Integrity, privacy and output handling

- Artifacts identified by per-file hashes + deterministic manifest digest; rehash source after scan to catch drift.
- Raw scanner logs may contain absolute paths, tokens or sensitive metadata. Store only bounded evidence in mode-0700 output directory/mode-0600 files where available. Redact home directory/usernames and token-like strings from Markdown and console; provide optional full raw evidence only under explicit local privacy settings, not in public issues.
- JSON reports are not signed attestations in MVP; digests detect accidental modification if a trusted copy of hash exists but do not authenticate creator. No tamper-proof claim.
- Do not upload model artifacts to issue trackers, cloud scanners, CI logs or telemetry. No telemetry unless separately approved and documented.
- Temporary snapshot and scanner workdir must be cleaned in `finally` without following untrusted symlinks; no hidden persistent cache.

## Dependency and contributor hygiene

- Commit `uv.lock` after resolution; review added dependency's license, provenance, published security advisories and install-time behavior. Avoid install-time scripts from unverified sources.
- No secrets in tests or docs; pin CI actions to reviewed commit hashes; use least-privilege CI tokens and no untrusted fork secrets.
- Security regressions are release blockers even when code coverage passes. No claiming third-party product security conclusions from marketing pages alone.

## Vulnerability reporting (once repository is public)

Until maintainers publish a private disclosure address or GitHub private vulnerability reporting is enabled, **do not disclose zero-day exploit details in public project issues**. Use the repository's private vulnerability-report channel when available; otherwise contact maintainers through an agreed private channel. Maintainers should acknowledge receipt, assess reproduction in a safe environment and coordinate responsible disclosure with affected upstreams. Do not promise arbitrary response SLA before a maintainer process exists.

## Claims policy

Permitted: accurate description of executed tests and supported formats/versions, documented failures and limitations. Prohibited: perfect malware detection, immunity to VM escape, unconditional license clearance, guaranteed artifact safety, fabricated benchmark superiority, or claiming planned features are shipped. Mark sample reports `ILLUSTRATIVE`.

## Platform support / threat caveats

Pure static MVP has hosted validation on Ubuntu 24.04/macOS 15 Intel, plus local macOS arm64 evidence; Windows remains unsupported. P2 microVM requires Linux/KVM/Firecracker with security hardening and independent review; it is not covered by current MVP claims. See `THREAT_MODEL.md` for 20 attack scenarios and residual risks.

## Release response

A confirmed fail-open security regression suspends release; document reproducer using harmless fixtures, add deterministic test, patch, rerun independent baseline and review whether prior verdicts were affected. If safety is unknowable, prefer `INSUFFICIENT` to silent success.

## PH-09 internal review — MV-024

The ordinary host has no model loader/dynamic artifact import path, checked by AST regressions and Ruff security rules. The single subprocess boundary uses fixed adapter argv, shell=False, a reviewed external version, sanitized environment, bounded pipes, process-group teardown and resource limits. Ruff S603 is suppressed only at that reviewed launch with a reason; AST tests enforce its boundary. A child that remains in the launched process group is killed even when its parent exits normally. A child that escapes the group remains a residual subprocess risk; this is not isolation.

Filesystem containment compares opened directory device/inode ancestry as well as spelling, closing case-alias paths on insensitive filesystems. Reports, snapshot staging, scanner binary parents and scanner workspaces use these checks. Remaining source changes are detected best effort before publication; no atomic global filesystem guarantee exists. Private raw data and exact relative artifact filenames may be sensitive; do not publish them. Effective operator policy/owners are preserved for audit and can themselves contain sensitive information. Report digests are not signatures; inspect reads a stored assertion rather than authenticating its producer.

The v1 policy has no proof of safe remote/custom loader behavior. Declared trust_remote_code=true or custom loader mapping yields unresolved evidence, not APPROVE/CONTROLS; source prohibitions may independently BLOCK. OSV query details, point-in-time limits, dependency notices and versions are in verification/MV-024 and MV-001/MV-010. No dependencies were added; all 30 original third-party core/dev version pins match the foundation snapshot. This internal review does not substitute for independent security acceptance. Darwin scanner memory enforcement and OS network isolation remain unavailable; required memory evidence stays insufficient.
