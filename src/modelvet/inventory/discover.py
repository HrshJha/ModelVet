"""Names and filesystem identities used by bounded descriptor-based discovery."""

import hashlib
import os
import stat
import unicodedata
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path

from modelvet.core.errors import (
    BudgetExceeded,
    InvalidInput,
    IOFailure,
    PathEscape,
    SnapshotChanged,
)
from modelvet.inventory.gate import ValidatedInput, open_directory


def validate_relpath(path: str) -> str:
    if (
        not path
        or path.startswith("/")
        or "\\" in path
        or any(part in {"", ".", ".."} for part in path.split("/"))
        or any(ord(char) < 32 or ord(char) == 127 for char in path)
        or unicodedata.normalize("NFC", path) != path
    ):
        raise PathEscape("Unsafe or noncanonical artifact path.")
    try:
        encoded = path.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise PathEscape("Artifact names must be valid UTF-8.") from exc
    if len(encoded) > 4096:
        raise PathEscape("Artifact path length exceeds the supported limit.")
    return path


def stat_identity(info: os.stat_result) -> tuple[int, ...]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_nlink,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


@dataclass(frozen=True)
class FileObservation:
    relpath: str
    size: int
    sha256: str


def observe_directory(
    source: ValidatedInput, destination: Path | None = None
) -> tuple[FileObservation, ...]:
    """Stream-hash regular files, optionally copying to an owned private destination."""
    entries: list[FileObservation] = []
    seen: set[str] = set()
    nodes = 0
    total = 0

    def read_file(fd: int, name: str, relative: str, before: os.stat_result) -> None:
        nonlocal total
        if before.st_nlink != 1 or before.st_size > source.limits.max_file_bytes:
            raise InvalidInput("Hardlinked or oversized input file.")
        handle = os.open(
            name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK, dir_fd=fd
        )
        try:
            opened = os.fstat(handle)
            if not stat.S_ISREG(opened.st_mode) or stat_identity(opened) != stat_identity(before):
                raise SnapshotChanged("Input file identity changed before reading.")
            digest = hashlib.sha256()
            count = 0
            with ExitStack() as stack:
                output = None
                if destination is not None:
                    target = os.open(
                        destination / relative, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
                    )
                    output = stack.enter_context(os.fdopen(target, "wb"))
                while True:
                    remaining = min(
                        source.limits.max_file_bytes - count,
                        source.limits.max_total_bytes - total,
                    )
                    chunk = os.read(handle, min(65536, remaining + 1))
                    if not chunk:
                        break
                    count += len(chunk)
                    total += len(chunk)
                    if remaining < len(chunk):
                        raise BudgetExceeded("Input byte budget exceeded.")
                    digest.update(chunk)
                    if output is not None:
                        output.write(chunk)
            if count != before.st_size or stat_identity(os.fstat(handle)) != stat_identity(before):
                raise SnapshotChanged("Input file changed while reading.")
            if destination is not None:
                os.chmod(destination / relative, 0o400)
            entries.append(FileObservation(relative, count, digest.hexdigest()))
        finally:
            os.close(handle)

    def walk(fd: int, relative: str, depth: int) -> None:
        nonlocal nodes
        if depth > 64:
            raise BudgetExceeded("Artifact directory depth exceeds 64.")
        before = os.fstat(fd)
        if before.st_dev != source.root_device:
            raise InvalidInput("Cross-device artifact traversal is not supported.")
        with os.scandir(fd) as items:
            for item in items:
                nodes += 1
                if nodes > source.limits.max_files:
                    raise BudgetExceeded("Artifact entry budget exceeded.")
                path = validate_relpath(f"{relative}/{item.name}" if relative else item.name)
                if path.casefold() in seen:
                    raise InvalidInput("Canonical or case-colliding artifact paths.")
                seen.add(path.casefold())
                info = os.stat(item.name, dir_fd=fd, follow_symlinks=False)
                if info.st_dev != source.root_device:
                    raise InvalidInput("Cross-device artifact entry.")
                if stat.S_ISDIR(info.st_mode):
                    child = os.open(
                        item.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
                    )
                    try:
                        if stat_identity(os.fstat(child)) != stat_identity(info):
                            raise SnapshotChanged("Input directory changed during discovery.")
                        if destination is not None:
                            (destination / path).mkdir(mode=0o700)
                        walk(child, path, depth + 1)
                    finally:
                        os.close(child)
                elif stat.S_ISREG(info.st_mode):
                    read_file(fd, item.name, path, info)
                else:
                    raise InvalidInput("Symlinks and special artifact entries are rejected.")
        if stat_identity(os.fstat(fd)) != stat_identity(before):
            raise SnapshotChanged("Input directory changed during discovery.")

    try:
        fd = open_directory(source.artifact_dir)
        try:
            info = os.fstat(fd)
            if (info.st_dev, info.st_ino) != (source.root_device, source.root_inode):
                raise SnapshotChanged("Input root changed after validation.")
            walk(fd, "", 0)
        finally:
            os.close(fd)
    except OSError as exc:
        raise IOFailure("Bounded filesystem observation failed.") from exc
    return tuple(sorted(entries, key=lambda item: item.relpath.encode()))
