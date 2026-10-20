"""Private bounded copy; never deserialize artifact contents."""

import os
import shutil
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from types import MappingProxyType

from modelvet.core.errors import InvalidInput, IOFailure
from modelvet.inventory.discover import FileObservation, observe_directory
from modelvet.inventory.gate import InputGate, ValidatedInput


@dataclass(frozen=True)
class Snapshot:
    root: Path
    files: tuple[FileObservation, ...]
    source: ValidatedInput

    @cached_property
    def file_map(self) -> Mapping[str, FileObservation]:
        return MappingProxyType({entry.relpath: entry for entry in self.files})


class Snapshotter:
    def __init__(self, temp_parent: Path | None = None) -> None:
        self.temp_parent = temp_parent

    @contextmanager
    def create(self, source: ValidatedInput) -> Iterator[Snapshot]:
        if not shutil.rmtree.avoids_symlink_attacks:
            raise InvalidInput("Secure temporary cleanup is unsupported on this platform.")
        parent = self.temp_parent or Path(tempfile.gettempdir()).resolve()
        InputGate().validate(source.artifact_dir, parent / ".modelvet-staging", source.limits)
        root = Path(tempfile.mkdtemp(prefix="modelvet-snapshot-", dir=parent))
        try:
            if root.is_relative_to(source.artifact_dir):
                raise InvalidInput("Snapshot staging must be outside the input directory.")
            os.chmod(root, 0o700)
            files = observe_directory(source, destination=root)
            yield Snapshot(root, files, source)
        except OSError as exc:
            raise IOFailure("Filesystem operation failed during bounded snapshot.") from exc
        finally:
            shutil.rmtree(root)
