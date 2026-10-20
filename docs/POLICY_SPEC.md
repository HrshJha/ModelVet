# Policy v1 — implemented PH-05 contract

Local TOML is data, bounded to 64 KiB, 4,096 parsed values and depth 16. Unknown fields, unsupported versions, duplicate keys/entries, unknown checks or controls and contradictory rules are rejected. An invalid explicitly selected file never falls back to defaults. Environment variables cannot select or weaken policy. CLI resource flags retain their separate hard ceilings; `[limits]` is not a policy v1 field.

## Fields

| Field | Contract |
|---|---|
| `schema_version` | Required `"1.0.0"` |
| `policy_id`, `policy_version` | Bounded identifier and positive decimal version string |
| `applicability_version` | Required `"2"`; format mapping is the owned classifier registry |
| `mandatory_checks`, `optional_checks` | Required disjoint arrays covering all nine known check IDs; identity/classification always mandatory |
| `prohibitions` | Required array of `{rule_id, category}` tables; supported category: `REPOSITORY_CODE` |
| `controls` | Required array of `{control_id, owner}` tables; nonempty printable owner |
| `control_rules` | Required array of `{rule_id, condition, control_ids}` tables; every referenced control must be declared and every declaration used |
| `required_claims` | Optional array, default empty; supported kinds LICENSE, PROVENANCE, DEPENDENCY; these require sourced declarations, not verification of their truth |

Known checks: `identity`, `classification`, `structural:safetensors`, `structural:zip`, `metadata:local`, `dependencies:declared`, `source:presence`, `modelscan`, `scanner:resources`. Requirement levels apply only where the independent registry makes a check applicable. Making a check optional does not prove it completed. A prohibited source condition still requires sufficient evidence to assess that predicate.

The packaged [default policy](../src/modelvet/policies/default.toml) requires every applicable check and LICENSE/PROVENANCE declarations, bans independently confirmed repository Python code, and defines no conditional controls. Empty/model-free inventories, unknown formats and signature mismatches remain insufficient. This intentionally excludes many unsupported real artifacts.

## Controls

| ID | Required deployment condition |
|---|---|
| `ISOLATED_LOADING` | Load only within a deployment isolation boundary approved and enforced by the named owner. ModelVet does not provision or certify that boundary. |
| `NO_CODE_IMPORT` | Deployment must prohibit importing repository code and enabling remote-code loading; the named owner enforces this restriction. |

Rule conditions are `MODEL_PRESENT` (safetensors, standalone pickle-like or PyTorch ZIP candidate), `SERIALIZED_MODEL` (pickle-like or ZIP), and `REPOSITORY_CODE`. One condition cannot be both prohibited and controlled. Duplicate conditions, rule IDs, categories or control IDs are invalid. Built-in evaluator rule IDs are reserved. A control decision includes the actual control IDs and owners; it does not assert that deployment enforcement was tested.

For example, to require isolation for serialized models, add the following to a complete policy, replacing its empty `controls` and `control_rules` arrays:

```toml
[[controls]]
control_id = "ISOLATED_LOADING"
owner = "Platform security"

[[control_rules]]
rule_id = "ISOLATE-SERIALIZED"
condition = "SERIALIZED_MODEL"
control_ids = ["ISOLATED_LOADING"]
```

## Evaluator proof and precedence

The evaluator accepts manifest, coverage, findings/conflicts and required keyword inputs `classifications`, `checks`, `claims`. It validates canonical manifest identity, recomputes coverage and compares each supplied coverage row. Reordering records never selects a favorable observation.

1. `BLOCK`: a configured repository-code prohibition has matching, complete, owned identity/classification/source-presence checks and consistent per-file coverage. Evidence references identify those exact checks. Integrity conflicts affecting this proof prevent the ban; unrelated incomplete checks may remain.
2. `INSUFFICIENT`: mandatory gaps, malformed coverage, unsupported formats, mismatches, missing required declarations or unresolved relevant conflicts/findings. Integrity conflicts cannot be made irrelevant with a flag. Resolution strings do not implement human exceptions.
3. `CONTROLS`: all mandatory predicates complete, no unresolved evidence, applicable controls with explicit owners.
4. `APPROVE`: all mandatory predicates complete, no unresolved evidence or applicable controls. This is scoped static policy approval.

Core check facts use executor `modelvet`, matching artifact digest, COMPLETE status and no error code. Identity details include `sha256`; classification details include `format_class` and boolean `mismatch`; source-presence details include `source_present=true`. Scanner checks use executor `modelscan`. These are owned normalization inputs, not fields to copy from arbitrary scanner JSON.

V1 has no independent malicious-operation adjudicator. All scanner findings, including records labeled CORROBORATED, remain unresolved unless a separate independently supported prohibition determines BLOCK. A severity, finding label or process exit cannot create approval or establish a ban. Source presence is a policy condition, not a malware claim.

The policy semantic digest is domain-separated SHA-256 over the normalized effective policy. Comments, whitespace and entry ordering do not affect it; owner/rule/requirement changes do. `schemas/policy-v1.json` and `schemas/decision-v1.json` describe typed records; model validators additionally enforce cross-field invariants. Report hashing and scan integration are implemented in the local candidate.

## Validation command

```sh
uv run modelvet policy validate src/modelvet/policies/default.toml --json
```

Success: exit 0, bounded JSON with policy ID/version/digest, no file paths or policy contents. Human success uses stderr. Invalid input: exit 40, controlled stderr and empty stdout, including with `--json`. No scanner, model loader, network service or report writer is called.

Remote/custom loader declarations (trust_remote_code=true or custom loader mapping) remain unresolved under static v1. No scanner label or deployment control proves loader behavior.
