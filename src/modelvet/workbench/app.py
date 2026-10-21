"""Authenticated optional HTTP adapter for the local static engine."""

import hashlib
import os
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from modelvet import __version__
from modelvet.core.config import PolicyValidator, load_policy
from modelvet.core.diagnostics import diagnose
from modelvet.core.errors import InvalidInput
from modelvet.workbench.jobs import Busy, Jobs
from modelvet.workbench.models import (
    Capabilities,
    DirectoryPage,
    JobRecord,
    PolicyRequest,
    PolicyResponse,
    ReportPage,
    ReportSummary,
    ScanInput,
    SessionRequest,
    SessionResponse,
)
from modelvet.workbench.paths import Workspace, read_private, write_private
from modelvet.workbench.review import router as review_router
from modelvet.workbench.review import selected_report
from modelvet.workbench.security import COOKIE, BrowserSession, LocalBoundary
from modelvet.workbench.store import Store


def create_app(
    models_root: Path, workspace_path: Path, origin: str, *, launch_token: str | None = None
) -> FastAPI:
    session = BrowserSession(origin, launch_token)
    workspace = Workspace(models_root, workspace_path)
    try:
        store = Store(workspace)
        jobs = Jobs(store)
        # Probe before the HTTP server/request thread pool starts. Scanner preexec
        # resource setup must not fork from a multithreaded request handler.
        capability_snapshot = diagnose(excluded_roots=(workspace.models_root, workspace.root))
    except BaseException:
        workspace.close()
        raise

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            jobs.close()
            store.close()
            workspace.close()

    app = FastAPI(
        title="ModelVet Workbench",
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )
    app.state.workspace, app.state.browser_session = workspace, session
    app.state.store, app.state.jobs = store, jobs
    app.add_middleware(LocalBoundary, session=session)

    @app.exception_handler(Exception)
    async def unexpected(request: Request, error: Exception) -> JSONResponse:
        return JSONResponse(
            {
                "error": "INTERNAL_FAILURE",
                "message": "The local operation failed. No successful result is inferred.",
            },
            status_code=500,
        )

    @app.exception_handler(Busy)
    async def busy(request: Request, error: Busy) -> JSONResponse:
        return JSONResponse(
            {
                "error": "JOB_CONFLICT",
                "message": "A scan is already running, stopping, or has finished.",
            },
            status_code=409,
        )

    @app.exception_handler(sqlite3.Error)
    async def storage_error(request: Request, error: sqlite3.Error) -> JSONResponse:
        return JSONResponse(
            {
                "error": "STORAGE_FAILURE",
                "message": "Private history storage is unavailable. No successful job is inferred.",
            },
            status_code=500,
        )

    @app.exception_handler(RequestValidationError)
    async def invalid_fields(request: Request, error: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            {"error": "INVALID_FIELDS", "message": "Check the request fields and reviewed limits."},
            status_code=422,
        )

    @app.exception_handler(InvalidInput)
    @app.exception_handler(ValidationError)
    async def invalid_input(request: Request, error: InvalidInput) -> JSONResponse:
        return JSONResponse(
            {
                "error": "INVALID_INPUT",
                "message": "Selected folder, policy or report is missing, changed or unsafe.",
            },
            status_code=400,
        )

    @app.exception_handler(OSError)
    async def io_error(request: Request, error: OSError) -> JSONResponse:
        return JSONResponse(
            {"error": "IO_FAILURE", "message": "Local data could not be safely read or written."},
            status_code=400,
        )

    @app.post("/api/v1/session", response_model=SessionResponse)
    def exchange(body: SessionRequest) -> JSONResponse:
        if not session.exchange(body.token):
            raise HTTPException(401, "Launch token is invalid or already used.")
        response = JSONResponse(SessionResponse(csrf_token=session.csrf).model_dump())
        response.set_cookie(
            COOKIE, session.session_id, httponly=True, samesite="strict", path="/api/"
        )
        return response

    @app.get("/api/v1/session", response_model=SessionResponse)
    def current_session() -> SessionResponse:
        return SessionResponse(csrf_token=session.csrf)

    @app.get("/api/v1/capabilities", response_model=Capabilities)
    def capabilities() -> Capabilities:
        result = capability_snapshot
        return Capabilities(
            version=__version__,
            models_root_label=workspace.models_root.name,
            scanner_available=result["scanner_available"],
            scanner_version=result["scanner_version"],
            serialized_scan_ready=result["serialized_scan_ready"],
            hub_token_configured=bool(os.environ.get("HF_TOKEN")),
            limitations=result["limitations"],
        )

    @app.get("/api/v1/directories", response_model=DirectoryPage)
    def directories(
        path: str = ".",
        offset: int = Query(0, ge=0, le=10000),
        limit: int = Query(100, ge=1, le=100),
    ) -> DirectoryPage:
        return workspace.directories(path, offset, limit)

    @app.get("/api/v1/policy", response_model=PolicyResponse)
    def default_policy() -> PolicyResponse:
        policy = load_policy()
        return PolicyResponse(
            id="default",
            policy_id=policy.policy_id,
            policy_digest=policy.semantic_digest,
            mandatory_checks=list(policy.mandatory_checks),
            required_claims=list(policy.required_claims),
        )

    @app.post("/api/v1/policies", response_model=PolicyResponse)
    def policy_import(body: PolicyRequest) -> PolicyResponse:
        workspace.check()
        raw = body.toml.encode("utf-8", errors="strict")
        policy = PolicyValidator().parse(raw)
        key = hashlib.sha256(raw).hexdigest()
        target = workspace.root / "policies" / f"{key}.toml"
        try:
            write_private(target, raw)
        except FileExistsError:
            if read_private(target, 65536) != raw:
                raise InvalidInput("Stored policy identity changed.") from None
        return PolicyResponse(
            id=key,
            policy_id=policy.policy_id,
            policy_digest=policy.semantic_digest,
            mandatory_checks=list(policy.mandatory_checks),
            required_claims=list(policy.required_claims),
        )

    @app.post("/api/v1/scans", response_model=JobRecord, status_code=202)
    def start_scan(body: ScanInput) -> JobRecord:
        return jobs.start(body)

    @app.get("/api/v1/scans/active", response_model=JobRecord | None)
    def active_scan() -> JobRecord | None:
        key = jobs.active_id
        return jobs.current(key) if key is not None else None

    @app.get("/api/v1/scans/{job_id}", response_model=JobRecord)
    def scan_status(job_id: str) -> JobRecord:
        return jobs.current(job_id)

    @app.post("/api/v1/scans/{job_id}/cancel", response_model=JobRecord)
    def cancel_scan(job_id: str) -> JobRecord:
        return jobs.cancel(job_id)

    @app.get("/api/v1/reports", response_model=ReportPage)
    def history(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100)) -> ReportPage:
        return store.reports(offset, limit)

    @app.get("/api/v1/reports/{report_id}", response_model=ReportSummary)
    def report_summary(report_id: str) -> ReportSummary:
        return selected_report(store, report_id)[2]

    app.include_router(review_router(store))

    assets = Path(__file__).parent / "static"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets / "assets"), name="assets")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        if not (assets / "index.html").is_file():
            raise HTTPException(
                503, "Workbench assets are not built. Run the documented frontend build."
            )
        return FileResponse(assets / "index.html")

    return app
