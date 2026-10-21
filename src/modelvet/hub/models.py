"""Versioned remote source records; upstream IDs remain source claims."""

import unicodedata
from pathlib import PurePosixPath
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from modelvet.evidence.models import SHA256, WireModel
from modelvet.hub.reference import HubReference


def safe_path(value: str) -> str:
    if (
        not value
        or len(value.encode("utf-8")) > 1024
        or value.startswith("/")
        or "\\" in value
        or any(ord(c) < 32 or ord(c) == 127 for c in value)
        or any(p in {"", ".", ".."} for p in value.split("/"))
        or unicodedata.normalize("NFC", value) != value
        or any(p.endswith((" ", ".")) or ":" in p for p in value.split("/"))
        or len(PurePosixPath(value).parts) > 32
    ):
        raise ValueError("Unsafe repository path.")
    return value


class HubFile(WireModel):
    path: str
    size: Annotated[int, Field(ge=0, le=2**63 - 1)]
    blob_id: Annotated[str, Field(pattern=r"^[a-f0-9]{40}$")]
    lfs_sha256: SHA256 | None = None
    sha256: SHA256 | None = None
    status: Literal["INVENTORIED", "RETRIEVED", "OVERSIZED", "BUDGET", "FAILED"] = "INVENTORIED"
    reason: Annotated[str | None, Field(max_length=256)] = None
    required_checks: tuple[str, ...] = ("identity", "classification")

    @model_validator(mode="after")
    def valid(self) -> Self:
        safe_path(self.path)
        from modelvet.policies.models import CHECK_IDS

        if not {"identity", "classification"} <= set(self.required_checks) <= CHECK_IDS:
            raise ValueError("Remote required-check references are invalid.")
        if len(set(self.required_checks)) != len(self.required_checks):
            raise ValueError("Duplicate remote required-check reference.")
        if (self.status == "RETRIEVED") != (self.sha256 is not None):
            raise ValueError("Retrieved content must have a local hash.")
        return self


class HubSource(WireModel):
    kind: Literal["huggingface"] = "huggingface"
    url: str
    repo_id: str
    requested_revision: str | None
    resolved_commit: Annotated[str, Field(pattern=r"^[a-f0-9]{40}$")]
    metadata_digest: SHA256
    transport: Literal["modelvet-https/1"] = "modelvet-https/1"
    inventory_complete: bool = True
    files: Annotated[tuple[HubFile, ...], Field(max_length=10000)]
    max_file_bytes: Annotated[int, Field(ge=1, le=1024**3)]
    max_total_bytes: Annotated[int, Field(ge=1, le=2 * 1024**3)]
    wall_time_s: Annotated[int, Field(ge=1, le=600)]
    cache: Literal["disabled"] = "disabled"

    @property
    def complete(self) -> bool:
        return self.inventory_complete and all(f.status == "RETRIEVED" for f in self.files)

    @model_validator(mode="after")
    def valid(self) -> Self:
        reference = HubReference.parse(self.url, self.requested_revision)
        if reference.repo_id != self.repo_id or reference.url != self.url:
            raise ValueError("Remote source identity is inconsistent.")
        keys = [f.path.casefold() for f in self.files]
        if len(set(keys)) != len(keys) or list(self.files) != sorted(
            self.files, key=lambda f: f.path
        ):
            raise ValueError("Remote inventory is ambiguous or unsorted.")
        if sum(f.size for f in self.files if f.status == "RETRIEVED") > self.max_total_bytes or any(
            f.size > self.max_file_bytes for f in self.files if f.status == "RETRIEVED"
        ):
            raise ValueError("Remote retrieval exceeds its declared resource ceilings.")
        return self
