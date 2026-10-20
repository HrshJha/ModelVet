"""Bounded snapshot reads with descriptor-based containment and drift checks."""

import os
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO

from modelvet.core.errors import InvalidInput, IOFailure, SnapshotChanged
from modelvet.core.snapshot import Snapshot
from modelvet.inventory.discover import stat_identity, validate_relpath
from modelvet.inventory.gate import open_directory
from modelvet.inventory.identity import ArtifactFile


@contextmanager
def open_snapshot_file(snapshot: Snapshot, file: ArtifactFile) -> Iterator[BinaryIO]:
    validate_relpath(file.relpath)
    entry = snapshot.file_map.get(file.relpath)
    if entry is None or (entry.size, entry.sha256) != (file.size, file.sha256):
        raise InvalidInput("Requested file is not in the frozen snapshot inventory.")
    try:
        parent = open_directory(snapshot.root / Path(file.relpath).parent)
        try:
            handle = os.open(
                Path(file.relpath).name,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                dir_fd=parent,
            )
        finally:
            os.close(parent)
        with os.fdopen(handle, "rb", buffering=0) as stream:
            before = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_nlink != 1
                or before.st_size != file.size
            ):
                raise SnapshotChanged("Snapshot file type or size changed.")
            yield stream
            if stat_identity(os.fstat(stream.fileno())) != stat_identity(before):
                raise SnapshotChanged("Snapshot file changed during a bounded read.")
    except OSError as exc:
        raise IOFailure("Snapshot read failed or encountered an unsafe path.") from exc


def read_prefix(snapshot: Snapshot, file: ArtifactFile, limit: int) -> bytes:
    if not 0 <= limit <= snapshot.source.limits.max_metadata_bytes:
        raise InvalidInput("Read exceeds the metadata ceiling.")
    with open_snapshot_file(snapshot, file) as stream:
        return stream.read(min(file.size, limit))
