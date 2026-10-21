"""Versioned browser contracts, separate from admission evidence."""

from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class SessionRequest(ApiModel):
    token: Annotated[str, Field(min_length=32, max_length=128)]


class SessionResponse(ApiModel):
    csrf_token: str
    api_version: Literal["1"] = "1"


class DirectoryEntry(ApiModel):
    name: str
    relpath: str
    selectable: bool
    kind: Literal["directory", "unavailable"]


class DirectoryPage(ApiModel):
    relpath: str
    entries: list[DirectoryEntry]
    total: int
    offset: int
    limit: int


class PolicyRequest(ApiModel):
    toml: Annotated[str, Field(min_length=1, max_length=65536)]


class PolicyResponse(ApiModel):
    id: str
    policy_id: str
    policy_digest: str
    mandatory_checks: list[str]
    required_claims: list[str]


class ScanInput(ApiModel):
    model_path: Annotated[str, Field(max_length=4096)] = ""
    hub_url: Annotated[str | None, Field(max_length=512)] = None
    revision: Annotated[str | None, Field(max_length=200)] = None
    use_hf_token: bool = False
    policy_id: Annotated[str, Field(max_length=80)] = "default"
    scanner: Literal["auto", "modelscan", "none"] = "auto"
    max_files: Annotated[int, Field(ge=1, le=10000)] = 10000
    max_file_mib: Annotated[int, Field(ge=1, le=1024)] = 1024
    max_total_mib: Annotated[int, Field(ge=1, le=2048)] = 2048
    timeout_sec: Annotated[int, Field(ge=1, le=120)] = 120

    @model_validator(mode="after")
    def selected_input(self) -> Self:
        if bool(self.model_path) == bool(self.hub_url):
            raise ValueError("Choose one local folder or Hugging Face URL.")
        if self.hub_url:
            from modelvet.core.errors import InvalidInput
            from modelvet.hub.reference import HubReference

            try:
                HubReference.parse(self.hub_url, self.revision)
            except InvalidInput as error:
                raise ValueError(str(error)) from None
        elif self.revision is not None or self.use_hf_token:
            raise ValueError("Hub revision/auth options require a Hub URL.")
        return self


class JobRecord(ApiModel):
    id: str
    label: str
    status: Literal["running", "cancelling", "completed", "cancelled", "failed", "interrupted"]
    stage: str
    started_at: str
    elapsed_seconds: float = 0
    error_code: str | None = None
    report_id: str | None = None
    model_path: str | None = None
    hub_url: str | None = None


class Guidance(ApiModel):
    id: str
    title: str
    explanation: str
    action: str
    check_id: str | None = None
    rule_id: str | None = None


class ReportSummary(ApiModel):
    id: str
    label: str
    created_at: str
    decision: str
    reason: str
    rule_ids: list[str]
    manifest_digest: str
    semantic_digest: str
    policy_id: str
    file_count: int
    policy_version: str = ""
    policy_digest: str = ""
    total_bytes: int
    required_complete: int
    required_total: int
    findings_count: int
    conflicts_count: int
    demo: bool = False
    guidance: list[Guidance] = []
    controls: list[dict[str, str]] = []
    limitations: list[str] = []
    model_path: str | None = None
    hub_source: dict[str, Any] | None = None


class ReportPage(ApiModel):
    items: list[ReportSummary]
    total: int
    offset: int
    limit: int


class EvidencePage(ApiModel):
    section: str
    items: list[dict[str, Any]]
    total: int
    offset: int
    limit: int
    truncated: bool = False


class CompareInput(ApiModel):
    before_id: str
    after_id: str
    show_paths: bool = False


class Capabilities(ApiModel):
    version: str
    models_root_label: str
    scanner_available: bool
    scanner_version: str | None
    serialized_scan_ready: bool
    hub_available: bool = True
    hub_token_configured: bool = False
    limitations: list[str]
