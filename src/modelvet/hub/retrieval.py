"""Explicit, sequential per-file transfer to a private descriptor-relative stage."""

import hashlib
import os
import shutil
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from modelvet.core.errors import InvalidInput
from modelvet.core.limits import MIB
from modelvet.hub.client import HubClient
from modelvet.hub.models import HubFile, HubSource
from modelvet.hub.reference import HubReference
from modelvet.hub.transport import HTTPS, HubError
from modelvet.inventory.gate import open_directory


@dataclass(frozen=True)
class HubLimits:
    max_files: int = 10000
    max_file_bytes: int = 1024 * MIB
    max_total_bytes: int = 2048 * MIB
    wall_time_s: int = 600

    def __post_init__(self) -> None:
        if not (
            1 <= self.max_files <= 10000
            and 1 <= self.max_file_bytes <= 1024 * MIB
            and 1 <= self.max_total_bytes <= 2048 * MIB
            and 1 <= self.wall_time_s <= 600
        ):
            raise InvalidInput("Hub retrieval limits exceed the supported hard ceilings.")


def required_for_path(path: str) -> tuple[str, ...]:
    suffix = Path(path).suffix.lower()
    extra = {
        ".safetensors": ("structural:safetensors",),
        ".pt": ("structural:zip", "modelscan", "scanner:resources"),
        ".pth": ("structural:zip", "modelscan", "scanner:resources"),
        ".bin": ("modelscan", "scanner:resources"),
        ".pkl": ("modelscan", "scanner:resources"),
        ".pickle": ("modelscan", "scanner:resources"),
        ".zip": ("structural:zip", "modelscan", "scanner:resources"),
        ".json": ("metadata:local",),
        ".md": ("metadata:local",),
        ".txt": ("metadata:local",),
        ".py": ("source:presence",),
    }.get(suffix, ())
    if Path(path).name.upper() in {"LICENSE", "NOTICE", "COPYING"}:
        extra = tuple(sorted(set(extra) | {"metadata:local"}))
    if path == "modelvet-environment.json":
        extra += ("dependencies:declared",)
    return ("identity", "classification", *extra)


def parent_fd(root: int, path: str) -> tuple[int, str]:
    parts = path.split("/")
    current = os.dup(root)
    try:
        for part in parts[:-1]:
            try:
                os.mkdir(part, mode=0o700, dir_fd=current)
            except FileExistsError:
                pass
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current)
            os.close(current)
            current = child
        return current, parts[-1]
    except BaseException:
        os.close(current)
        raise


def retrieve(
    reference: HubReference,
    root: Path,
    limits: HubLimits,
    transport: HTTPS,
    on_progress: Callable[[str], None] | None = None,
) -> HubSource:
    source = HubClient(transport).inventory(
        reference,
        max_files=limits.max_files,
        max_file_bytes=limits.max_file_bytes,
        max_total_bytes=limits.max_total_bytes,
        wall_time_s=limits.wall_time_s,
    )
    if on_progress:
        on_progress("hub_retrieval")
    # Stage is freshly created by the caller, never a caller-selected artifact path.
    root_fd = open_directory(root)
    remaining = limits.max_total_bytes
    rows: list[HubFile] = []
    planned = min(
        sum(f.size for f in source.files if f.size <= limits.max_file_bytes), limits.max_total_bytes
    )
    stopped_reason = (
        "Insufficient private staging space for retrieval and scan snapshot."
        if shutil.disk_usage(root).free < 2 * planned + 32 * MIB
        else None
    )
    try:
        for file in source.files:
            file = file.model_copy(update={"required_checks": required_for_path(file.path)})
            if stopped_reason is not None:
                rows.append(file.model_copy(update={"status": "FAILED", "reason": stopped_reason}))
                continue
            if file.size > limits.max_file_bytes:
                rows.append(
                    file.model_copy(
                        update={"status": "OVERSIZED", "reason": "Per-file byte limit."}
                    )
                )
                continue
            if file.size > remaining:
                rows.append(
                    file.model_copy(
                        update={"status": "BUDGET", "reason": "Aggregate transfer byte limit."}
                    )
                )
                continue
            parent, name = parent_fd(root_fd, file.path)
            temp_name = ".modelvet-partial-" + uuid.uuid4().hex
            descriptor = -1
            received = 0
            try:
                descriptor = os.open(
                    temp_name,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=parent,
                )
                sha256 = hashlib.sha256()
                blob = hashlib.sha1(f"blob {file.size}\0".encode(), usedforsecurity=False)
                url = (
                    f"https://huggingface.co/{quote(reference.repo_id, safe='/')}/resolve/"
                    f"{source.resolved_commit}/{quote(file.path, safe='/')}"
                )
                with transport.response(url) as response:
                    commit = response.getheader("X-Repo-Commit")
                    if commit is not None and commit != source.resolved_commit:
                        raise HubError("Retrieved revision changed.")
                    length = response.getheader("Content-Length")
                    if length is not None and (not length.isdigit() or int(length) != file.size):
                        raise HubError("Transfer size disagrees with inventory.")
                    while True:
                        chunk = transport.read(response, min(65536, file.size - received + 1))
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        received += len(chunk)
                        if received > file.size or remaining < 0:
                            raise HubError("Transfer exceeded the inventory or byte budget.")
                        view = memoryview(chunk)
                        while view:
                            written = os.write(descriptor, view)
                            if written <= 0:
                                raise OSError("Short staging write.")
                            view = view[written:]
                        sha256.update(chunk)
                        blob.update(chunk)
                if received != file.size:
                    raise HubError("Truncated repository file.")
                if (file.lfs_sha256 is not None and sha256.hexdigest() != file.lfs_sha256) or (
                    file.lfs_sha256 is None and blob.hexdigest() != file.blob_id
                ):
                    raise HubError(
                        "Downloaded content disagrees with the upstream content identifier."
                    )
                os.fsync(descriptor)
                os.close(descriptor)
                descriptor = -1
                # Non-overwriting atomic promotion; no partial file enters the scan.
                os.link(
                    temp_name, name, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False
                )
                os.unlink(temp_name, dir_fd=parent)
                os.fsync(parent)
                rows.append(
                    file.model_copy(update={"status": "RETRIEVED", "sha256": sha256.hexdigest()})
                )
            except (OSError, InvalidInput, ValueError) as error:
                # Never copy network exception text, signed URLs or response bodies into reports.
                reason = "Transfer, content identity, deadline or private storage check failed."
                rows.append(file.model_copy(update={"status": "FAILED", "reason": reason}))
                if time.monotonic() >= transport.deadline:
                    stopped_reason = (
                        "Network boundary, transfer or assessment deadline unavailable."
                    )
                if isinstance(error, OSError):
                    stopped_reason = "Private retrieval storage unavailable."
            finally:
                if descriptor >= 0:
                    os.close(descriptor)
                try:
                    os.unlink(temp_name, dir_fd=parent)
                except FileNotFoundError:
                    pass
                os.close(parent)
    finally:
        os.close(root_fd)
    return source.model_copy(update={"files": tuple(rows)})
