"""The observed ModelScan 0.8.8 report schema, not a generic scanner schema."""

from typing import Self

from pydantic import Field, JsonValue, model_validator

from modelvet.evidence.models import WireModel


class Scanned(WireModel):
    total_scanned: int = Field(ge=0)
    scanned_files: tuple[str, ...] = ()


class SkippedFile(WireModel):
    category: str
    description: str
    source: str


class Skipped(WireModel):
    total_skipped: int = Field(ge=0)
    skipped_files: tuple[SkippedFile, ...] = ()


class Summary(WireModel):
    total_issues_by_severity: dict[str, int]
    total_issues: int = Field(ge=0)
    input_path: str
    absolute_path: str
    modelscan_version: str
    timestamp: str
    scanned: Scanned
    skipped: Skipped


class Issue(WireModel):
    description: str = Field(max_length=4096)
    operator: str
    module: str
    source: str
    scanner: str
    severity: str


class ModelScanPayload(WireModel):
    summary: Summary
    issues: tuple[Issue, ...]
    errors: tuple[dict[str, JsonValue], ...]

    @model_validator(mode="after")
    def counts_agree(self) -> Self:
        summary = self.summary
        if (
            summary.scanned.total_scanned != len(summary.scanned.scanned_files)
            or summary.skipped.total_skipped != len(summary.skipped.skipped_files)
            or summary.total_issues != len(self.issues)
            or len(set(summary.scanned.scanned_files)) != len(summary.scanned.scanned_files)
        ):
            raise ValueError("Scanner counts or duplicate paths are inconsistent.")
        counts = {
            severity: sum(issue.severity == severity for issue in self.issues)
            for severity in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
        }
        if summary.total_issues_by_severity != counts or sum(counts.values()) != len(self.issues):
            raise ValueError("Scanner severity totals contradict issue records.")
        return self
