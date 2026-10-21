"""Escape all untrusted text as entity-encoded Markdown text."""

from modelvet.reports.json_report import Report


def escape(value: object) -> str:
    text = str(value)
    return "".join(
        c if c.isalnum() or c in " -_" else f"&#{ord(c)};"
        for c in text.replace("\n", " ").replace("\r", " ")
    )


def render_markdown(report: Report) -> str:
    lines = [
        "# ModelVet static assessment",
        "",
        f"## {report.decision.state.value}",
        "",
        escape(report.decision.reason),
        "",
        "## Artifact and policy",
        "",
        f"Manifest: {escape(report.manifest_digest)}",
        "",
        f"Policy: {escape(report.policy.policy_id)} v{escape(report.policy.policy_version)}",
        "",
        f"Policy digest: {escape(report.policy_digest)}",
        "",
        f"Semantic digest: {escape(report.semantic_digest)}",
        "",
        "## Decision evidence",
        "",
    ]
    lines.extend(f"- {escape(rule)}" for rule in report.decision.rule_ids)
    lines.extend(
        f"- {escape(ref)} → {escape(report.references[ref])}"
        for ref in report.decision.evidence_refs
    )
    lines += ["", "## Required controls", ""]
    lines.extend(
        f"- {escape(c.control_id)} — owner: {escape(c.owner)}"
        for c in report.decision.required_controls
    )
    if report.source is not None:
        source = report.source
        lines += [
            "",
            "## Hugging Face source",
            "",
            escape(source.url),
            "",
            f"Pinned commit: {source.resolved_commit}",
            "",
            f"Requested revision: {escape(source.requested_revision or 'default')}",
            "",
            f"Metadata digest: {source.metadata_digest}",
            "",
            "Transfer completion is not check coverage. Upstream IDs are source claims.",
            "",
            "| Repository file | Bytes | Retrieval | Required checks | Reason |",
            "|---|---:|---|---|---|",
        ]
        lines.extend(
            f"| {escape(f.path)} | {f.size} | {f.status} | "
            f"{escape(', '.join(f.required_checks))} | {escape(f.reason or '')} |"
            for f in source.files
        )
    lines += [
        "",
        "## File identity",
        "",
        "| File | SHA-256 | Bytes | Format |",
        "|---|---|---:|---|",
    ]
    lines.extend(
        f"| {escape(f.relpath)} | {f.sha256} | {f.size} | {f.format_class.value} |"
        for f in report.files
    )
    lines += [
        "",
        "## Coverage",
        "",
        "| File ID | Complete | Required unresolved |",
        "|---|---|---|",
    ]
    lines.extend(
        f"| {r.file_id} | {escape(', '.join(r.completed_check_ids))} | "
        f"{escape(', '.join(r.mandatory_unresolved))} |"
        for r in report.coverage
    )
    lines += ["", "## Check results", ""]
    lines.extend(
        f"- {escape(c.check_id)} / {c.file_id}: {c.status.value}, {c.result.value}; "
        f"{escape(c.reason or '')}"
        for c in report.checks
    )
    lines += ["", "## Findings", ""]
    lines.extend(
        f"- {f.severity.value} {f.verification_state.value}: {escape(f.description)} "
        f"({escape(f.source_ref)}; file {f.file_id}; check {escape(f.check_id)})"
        for f in report.findings
    )
    lines += ["", "## Local declarations and dependencies", ""]
    lines.extend(
        f"- {c.kind}: {escape(c.value)} ({escape(c.source_ref)}; {c.confidence})"
        for c in report.claims
    )
    lines.extend(
        f"- {escape(d.name)} {escape(d.version or 'UNKNOWN')}: {d.status}"
        for d in report.dependencies
    )
    lines += ["", "## Conflicts", ""]
    lines.extend(f"- {c.type}: {escape(c.reason)} ({c.conflict_id})" for c in report.conflicts)
    lines += ["", "## Tools and executions", ""]
    lines.extend(
        f"- {escape(tool.tool_id)} {escape(tool.version)}: {escape(tool.source)}"
        for tool in report.tools
    )
    lines.extend(
        f"- {escape(item.execution_id)}: {item.status}, exit {item.exit_code}; "
        f"{escape(item.reason or '')}"
        for item in report.executions
    )
    lines += ["", "## Exceptions", "", "No human overrides applied.", "", "## Raw evidence", ""]
    lines.extend(
        f"- {r.digest}: {escape(r.filename)} ({r.size} bytes; restricted original bytes)"
        for r in report.raw_evidence
    )
    lines += ["", "## Limitations", ""]
    lines.extend(f"- {escape(s)}" for s in report.limitations)
    lines += [
        "",
        "## Reproduction metadata",
        "",
        f"ModelVet {escape(report.run.modelvet_version)}; "
        f"{escape(report.run.host_os_family)}; run {report.run.run_id}",
        "",
        f"Observed {escape(report.run.started_at)} to {escape(report.run.finished_at)}",
        "",
    ]
    return "\n".join(lines)
