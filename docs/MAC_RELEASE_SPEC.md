# Mac-first local preview — FR-028

## Authorized scope

On 2026-10-21 the maintainer explicitly requested focusing on the available Mac and changing requirements that block that delivery. The product is the local static CLI and optional authenticated browser Workbench. Local macOS arm64 and hosted macOS 15 Intel are the current verification targets. Python 3.12 and the UI extra are required for the Workbench; Node is development/build only.

PH-08 independent benchmark comparison and PH-11 isolated loading are **DEFERRED** and do not block this scoped product. Development pilot results remain INCONCLUSIVE. No Linux/KVM host, hidden holdout or independent reviewer is required to complete this limited Mac preview. If loader research is resumed, the existing security gate still applies. Other platforms are outside the current support promise; prior Ubuntu test records remain historical evidence.

## Preserved safety behavior

- Host code inspects bounded bytes and never deserializes models or imports artifact code.
- Supported safetensors structure and sourced declarations can complete without ModelScan when every applicable predicate completes.
- Repository source may independently BLOCK under the recorded policy.
- Unknown/malformed files, missing claims and missing mandatory scanner/resource proof remain INSUFFICIENT. Mac memory limitations must not be reclassified as complete or ignored.
- Guidance helps a Mac user inspect exact evidence or obtain an appropriate publisher-supplied artifact; it must not require switching to Linux, manufacture declarations or suggest loading unknown files to convert them.
- No automatic repairs, remote model download, telemetry, hosted account system or loader capability.

## Scoped release gate

Internal implementation review, actual unit/property/API/browser/fault tests, lint/types/schema drift, private package contents, dependency notices and fresh installed-package checks must pass. The required hosted gate runs on macOS 15 Intel; local arm64 evidence remains separately labeled. Human-independent security certification and comparative research are not claimed. Existing residual risks and scanner memory/network/archive limitations remain visible in documentation/reports.

A limited Mac preview may be packaged and handed off after these engineering checks without treating future research as a dependency. Keep repository visibility unchanged. Publication can use the existing repository's prerelease channel under the maintainer's prior authorization; no PyPI/account/visibility expansion is implied. Record exact source and distribution identities, tested scope and limitations. Earlier general-release review packets remain useful for future broader claims, not blockers to this explicitly narrowed preview.

## Acceptance

T-MAC-01 verifies stable requirement/task mapping, Mac CI without a Linux target prerequisite, safe Mac guidance, unchanged serialized-input incompleteness and supported safetensors decisions. Existing suites continue to exercise all four decisions and actual installed assets. Mark MV-045 complete only after actual passing evidence. Deferred tasks remain deferred.
