"""Read-only report projections, bounded previews and pinned comparison inputs."""

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, Query, Request
from fastapi.responses import Response

from modelvet.core.errors import InvalidInput
from modelvet.reports.audit import ReportAudit, verify_report
from modelvet.reports.compare import ReportComparison, compare_reports
from modelvet.reports.json_report import Report, parse_report
from modelvet.reports.markdown import render_markdown
from modelvet.workbench.guidance import summarize
from modelvet.workbench.models import CompareInput, EvidencePage, ReportSummary
from modelvet.workbench.paths import write_private
from modelvet.workbench.store import Store

Section = Literal[
    "files",
    "checks",
    "coverage",
    "findings",
    "claims",
    "conflicts",
    "dependencies",
    "executions",
    "tools",
    "references",
]
DEMO_IDS = ("demo-approve", "demo-controls", "demo-block", "demo-insufficient")


def demo_report(key: str) -> Report:
    if key not in DEMO_IDS:
        raise InvalidInput("Unknown demonstration identifier.")
    target = Path(__file__).parent / "demo" / f"{key}.json"
    return parse_report(target.read_bytes())


def selected_report(store: Store, key: str) -> tuple[Report, bytes, ReportSummary]:
    if key in DEMO_IDS:
        report = demo_report(key)
        return (
            report,
            report.model_dump_json().encode(),
            summarize(
                report, key, "Demonstration · " + report.decision.state.value.title(), demo=True
            ),
        )
    return store.report(key)


def evidence_page(
    report: Report,
    section: Section,
    offset: int,
    limit: int,
    query: str,
    file_id: str | None,
    status: str | None,
) -> EvidencePage:
    if file_id is not None and (
        len(file_id) != 64 or any(c not in "0123456789abcdef" for c in file_id)
    ):
        raise InvalidInput("Invalid evidence file identifier.")
    rows: list[dict[str, Any]]
    if section == "references":
        rows = [{"id": key, "pointer": value} for key, value in sorted(report.references.items())]
    else:
        rows = [row.model_dump(mode="json") for row in getattr(report, section)]
    if section == "files":
        coverage = {row.file_id: row for row in report.coverage}
        for row in rows:
            row["coverage"] = coverage[row["file_id"]].model_dump(mode="json")
    if file_id is not None:
        rows = [row for row in rows if row.get("file_id", row.get("source_file_id")) == file_id]
    if status is not None:
        if section == "files" and status in {"complete", "unresolved"}:
            rows = [
                row
                for row in rows
                if bool(coverage[row["file_id"]].mandatory_unresolved) == (status == "unresolved")
            ]
        else:
            rows = [row for row in rows if row.get("status") == status]
    if query:
        rows = [
            row
            for row in rows
            if query.casefold() in json.dumps(row, ensure_ascii=False).casefold()
        ]
    captured: list[dict[str, Any]] = []
    truncated = False
    for row in rows[offset : offset + limit]:
        encoded = json.dumps(row, ensure_ascii=False)
        if len(encoded.encode()) > 65536:
            truncated = True
            captured.append(
                {
                    "preview_truncated": True,
                    "preview": encoded[:4096],
                    "file_id": row.get("file_id"),
                    "check_id": row.get("check_id"),
                    "notice": "Download the complete JSON report for this record.",
                }
            )
        else:
            captured.append(row)
    return EvidencePage(
        section=section,
        items=captured,
        total=len(rows),
        offset=offset,
        limit=limit,
        truncated=truncated,
    )


def router(store: Store) -> APIRouter:
    routes = APIRouter(prefix="/api/v1")

    @routes.get("/demos", response_model=list[ReportSummary])
    def demos() -> list[ReportSummary]:
        return [
            selected_report(store, key)[2]
            for key in DEMO_IDS
            if (Path(__file__).parent / "demo" / f"{key}.json").is_file()
        ]

    @routes.get("/reports/{report_id}/evidence/{section}", response_model=EvidencePage)
    def evidence(
        report_id: str,
        section: Section,
        offset: int = Query(0, ge=0),
        limit: int = Query(50, ge=1, le=100),
        q: str = Query("", max_length=256),
        file_id: str | None = None,
        status: str | None = Query(None, max_length=32),
    ) -> EvidencePage:
        return evidence_page(
            selected_report(store, report_id)[0], section, offset, limit, q, file_id, status
        )

    @routes.post("/reports/import", response_model=ReportSummary, status_code=201)
    async def import_report(request: Request) -> ReportSummary:
        return store.import_report(await request.body())

    @routes.get("/reports/{report_id}/download")
    def download(report_id: str, format: Literal["json", "markdown"] = "json") -> Response:
        report, raw, _ = selected_report(store, report_id)
        content = raw if format == "json" else render_markdown(report).encode()
        suffix = "json" if format == "json" else "md"
        return Response(
            content,
            media_type="application/json" if format == "json" else "text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="modelvet-{report_id}.{suffix}"'
            },
        )

    @routes.post("/reports/{report_id}/verify", response_model=ReportAudit)
    def verify(report_id: str) -> ReportAudit:
        _, raw, _ = store.report(report_id)
        path = store.report_path(report_id)
        result = verify_report(path, expected_report_sha256=hashlib.sha256(raw).hexdigest())
        store.report(report_id)
        return result

    @routes.post("/comparisons", response_model=ReportComparison)
    def compare(body: CompareInput) -> ReportComparison:
        _, before, _ = store.report(body.before_id)
        _, after, _ = store.report(body.after_id)
        # Compare captured, pinned bytes using the existing comparison service.
        with tempfile.TemporaryDirectory(
            prefix="comparison-", dir=store.workspace.root / "staging"
        ) as directory:
            parent = Path(directory)
            old, new = parent / "before.json", parent / "after.json"
            write_private(old, before)
            write_private(new, after)
            result = compare_reports(old, new, show_paths=body.show_paths)
        store.report(body.before_id)
        store.report(body.after_id)
        return result

    return routes
