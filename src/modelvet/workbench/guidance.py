"""Deterministic explanations; these never amend evidence or admission."""

from modelvet.reports.json_report import Report
from modelvet.workbench.models import Guidance, ReportSummary

CHECK_ADVICE = {
    "identity": (
        "Confirm the artifact identity",
        "Use an unchanged local copy and rerun the assessment.",
    ),
    "classification": (
        "Review the file format",
        (
            "Check the actual format and any extension/signature mismatch. "
            "Unknown content remains unresolved."
        ),
    ),
    "structural:safetensors": (
        "Check safetensors structure",
        (
            "Obtain a complete, well-formed artifact from its declared "
            "source; do not load it to troubleshoot."
        ),
    ),
    "structural:zip": (
        "Review archive support",
        (
            "Use a supported archive subset. Unsupported members and archive "
            "coverage remain unresolved."
        ),
    ),
    "metadata:local": (
        "Review local declarations",
        (
            "Supply accurate, sourced license and provenance declarations. A "
            "declaration is not independent verification."
        ),
    ),
    "dependencies:declared": (
        "Review dependency declarations",
        (
            "Provide explicit pinned dependency declarations when required; "
            "do not infer installed versions."
        ),
    ),
    "source:presence": (
        "Review repository code",
        (
            "Review the source-presence evidence against the selected policy. "
            "ModelVet does not execute it."
        ),
    ),
    "modelscan": (
        "Make scanner evidence available",
        (
            "Install the separately pinned ModelScan environment and add its "
            "executable to PATH before launching ModelVet. Check skipped "
            "files and raw evidence."
        ),
    ),
    "scanner:resources": (
        "Review the Mac scanner limitation",
        (
            "Required scanner memory bounds are unavailable on macOS, so this check "
            "remains unresolved. Review the recorded evidence or ask the publisher "
            "for a supported safetensors artifact with accurate declarations. "
            "Do not load unknown files to convert them."
        ),
    ),
}
RULE_ADVICE = {
    "MISSING-CLAIM": (
        "Supply accurate sourced declarations",
        (
            "Resolve missing license/provenance claims using trustworthy "
            "source material; do not invent values to obtain approval."
        ),
    ),
    "UNRESOLVED-CONFLICT": (
        "Resolve conflicting evidence",
        (
            "Inspect each source and obtain a consistent artifact or "
            "policy-supported evidence. Conflicts are not resolved by "
            "choosing the favorable claim."
        ),
    ),
    "UNRESOLVED-FINDING": (
        "Review reported findings",
        (
            "Inspect the scanner evidence and obtain independent "
            "substantiation. A scanner allegation is not automatically a "
            "proven prohibition."
        ),
    ),
    "NO-MODEL": (
        "Choose a model artifact folder",
        "Select a directory containing a supported model artifact and its local metadata.",
    ),
    "INVALID-EVIDENCE": (
        "Repeat from a stable artifact",
        (
            "Investigate identity or evidence inconsistencies before "
            "rescanning an unchanged local copy."
        ),
    ),
}


def summarize(report: Report, key: str, label: str, *, demo: bool = False) -> ReportSummary:
    total = sum(len(row.mandatory_check_ids) for row in report.coverage)
    completed = sum(
        len(set(row.mandatory_check_ids) & set(row.completed_check_ids)) for row in report.coverage
    )
    advice: list[Guidance] = []
    for rule in report.decision.rule_ids:
        if rule in RULE_ADVICE:
            title, action = RULE_ADVICE[rule]
            advice.append(
                Guidance(
                    id=f"rule:{rule}",
                    title=title,
                    explanation=f"Admission rule {rule} applies to this stored report.",
                    action=action,
                    rule_id=rule,
                )
            )
    unresolved = sorted(
        {
            check
            for row in report.coverage
            for check in set(row.mandatory_check_ids) - set(row.completed_check_ids)
        }
    )
    for check in unresolved:
        title, action = CHECK_ADVICE.get(
            check,
            (
                "Review the unresolved check",
                "Inspect the recorded status and limitations before rerunning.",
            ),
        )
        advice.append(
            Guidance(
                id=f"check:{check}",
                title=title,
                explanation="This applicable mandatory check has no complete assessment.",
                action=action,
                check_id=check,
            )
        )
    if report.decision.state == "BLOCK":
        advice.insert(
            0,
            Guidance(
                id="decision:block",
                title="An explicit policy prohibition applies",
                explanation=report.decision.reason,
                action=(
                    "Inspect the cited rule and its evidence. Do not treat a policy "
                    "BLOCK as a demonstrated malicious-model detection."
                ),
            ),
        )
    if report.decision.required_controls:
        advice.append(
            Guidance(
                id="decision:controls",
                title="Enforce the named controls",
                explanation="Conditional admission requires the recorded owners and controls.",
                action=(
                    "Confirm that each owner can enforce the listed conditions before "
                    "deployment; ModelVet does not provision them."
                ),
            )
        )
    return ReportSummary(
        id=key,
        label=label,
        created_at=report.run.finished_at,
        decision=report.decision.state.value,
        reason=report.decision.reason,
        rule_ids=list(report.decision.rule_ids),
        manifest_digest=report.manifest_digest,
        semantic_digest=report.semantic_digest,
        policy_id=report.policy.policy_id,
        policy_version=report.policy.policy_version,
        policy_digest=report.policy_digest,
        file_count=report.artifact.file_count,
        total_bytes=report.artifact.total_bytes,
        required_complete=completed,
        required_total=total,
        findings_count=len(report.findings),
        conflicts_count=len(report.conflicts),
        demo=demo,
        guidance=advice,
        controls=[row.model_dump() for row in report.decision.required_controls],
        limitations=list(report.limitations),
    )
