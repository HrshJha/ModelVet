"""Private workspaces and descriptor-checked relative model selection."""

import fcntl
import os
import stat
from pathlib import Path

from modelvet.core.errors import InvalidInput
from modelvet.core.limits import ScanLimits
from modelvet.inventory.discover import stat_identity
from modelvet.inventory.gate import InputGate, absolute_path, has_ancestor_identity, open_directory
from modelvet.reports.writer import _directory
from modelvet.workbench.models import DirectoryEntry, DirectoryPage


def relative_path(value: str) -> Path:
    value.encode("utf-8", errors="strict")
    path = Path(value)
    if (
        not value
        or path.is_absolute()
        or ".." in path.parts
        or "\\" in value
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        raise InvalidInput("Select a relative directory within the configured model root.")
    return path


def read_private(path: Path, limit: int) -> bytes:
    parent = open_directory(path.parent)
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_nlink != 1
                or before.st_uid != os.geteuid()
                or stat.S_IMODE(before.st_mode) & 0o077
                or before.st_size > limit
            ):
                raise InvalidInput("Workspace file has unsafe permissions, type or size.")
            data = stream.read(limit + 1)
            if len(data) != before.st_size or stat_identity(before) != stat_identity(
                os.fstat(stream.fileno())
            ):
                raise InvalidInput("Workspace file changed during reading.")
            return data
    finally:
        os.close(parent)


def write_private(path: Path, data: bytes) -> None:
    parent = open_directory(path.parent)
    try:
        fd = os.open(
            path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent
        )
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(parent)


def trusted_worker_path(workspace: "Workspace") -> str:
    """Exclude model/workspace-controlled executable directories from PATH."""
    directories = []
    for entry in os.environ.get("PATH", "/usr/bin:/bin").split(os.pathsep):
        if not entry or not Path(entry).is_absolute():
            continue
        try:
            selected = Path(entry).resolve(strict=True)
            for root in (workspace.models_root, workspace.root):
                InputGate().validate(root, selected, ScanLimits())
            fd = open_directory(selected)
            os.close(fd)
            directories.append(str(selected))
        except (OSError, ValueError, InvalidInput):
            continue
    return os.pathsep.join(dict.fromkeys(directories))


class Workspace:
    def __init__(self, models_root: Path, root: Path) -> None:
        self.models_root = absolute_path(models_root)
        self.root = absolute_path(root)
        InputGate().validate(self.models_root, self.root, ScanLimits())
        model_fd = open_directory(self.models_root)
        try:
            info = os.fstat(model_fd)
            self.model_identity = (info.st_dev, info.st_ino)
            # Reject both directions, including aliases on insensitive filesystems.
            ancestor = open_directory(self.root, allow_missing=True)
            try:
                if self.models_root.is_relative_to(self.root):
                    raise InvalidInput("Model root and workspace must be separate directories.")
                if self.root.exists():
                    root_info = os.fstat(ancestor)
                    if has_ancestor_identity(model_fd, root_info.st_dev, root_info.st_ino):
                        raise InvalidInput("Workspace cannot contain the configured model root.")
            finally:
                os.close(ancestor)
        finally:
            os.close(model_fd)
        fd = _directory(self.root)
        try:
            info = os.fstat(fd)
            if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) & 0o077:
                raise InvalidInput("Workspace must be an owner-only directory.")
            self.identity = (info.st_dev, info.st_ino)
            self.lock_fd = os.open(
                ".owner.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600, dir_fd=fd
            )
            lock_info = os.fstat(self.lock_fd)
            if (
                not stat.S_ISREG(lock_info.st_mode)
                or lock_info.st_nlink != 1
                or lock_info.st_uid != os.geteuid()
                or stat.S_IMODE(lock_info.st_mode) & 0o077
            ):
                raise InvalidInput("Workspace ownership lock is unsafe.")
            try:
                fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise InvalidInput("Another workbench owns this workspace.") from exc
            for name in ("policies", "tasks", "reports", "imports", "staging"):
                try:
                    os.mkdir(name, 0o700, dir_fd=fd)
                except FileExistsError:
                    pass
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                try:
                    child_info = os.fstat(child)
                    if (
                        child_info.st_uid != os.geteuid()
                        or stat.S_IMODE(child_info.st_mode) & 0o077
                    ):
                        raise InvalidInput("Workspace subdirectories must be owner-only.")
                finally:
                    os.close(child)
        except BaseException:
            if hasattr(self, "lock_fd"):
                self.close()
            raise
        finally:
            os.close(fd)

    def close(self) -> None:
        if getattr(self, "lock_fd", -1) >= 0:
            os.close(self.lock_fd)
            self.lock_fd = -1

    def check(self) -> None:
        fd = open_directory(self.root)
        try:
            info = os.fstat(fd)
            if (
                (info.st_dev, info.st_ino) != self.identity
                or info.st_uid != os.geteuid()
                or stat.S_IMODE(info.st_mode) & 0o077
            ):
                raise InvalidInput("Workspace identity or permissions changed.")
        finally:
            os.close(fd)

    def model_path(self, value: str) -> Path:
        self.check()
        fd = open_directory(self.models_root)
        try:
            info = os.fstat(fd)
            if (info.st_dev, info.st_ino) != self.model_identity:
                raise InvalidInput("Configured model root changed.")
        finally:
            os.close(fd)
        path = self.models_root / relative_path(value)
        fd = open_directory(path)
        try:
            if not has_ancestor_identity(fd, *self.model_identity):
                raise InvalidInput("Selected directory escapes the model root.")
        finally:
            os.close(fd)
        return path

    def directories(self, value: str, offset: int, limit: int) -> DirectoryPage:
        path = self.model_path(value)
        fd = open_directory(path)
        entries = []
        try:
            before = stat_identity(os.fstat(fd))
            with os.scandir(fd) as iterator:
                for count, entry in enumerate(iterator):
                    if count >= 10000:
                        raise InvalidInput("Directory listing exceeds the entry limit.")
                    try:
                        entry.name.encode("utf-8", errors="strict")
                        relative_path(entry.name)
                        info = entry.stat(follow_symlinks=False)
                        directory = stat.S_ISDIR(info.st_mode)
                        if directory or not stat.S_ISREG(info.st_mode):
                            entries.append(
                                DirectoryEntry(
                                    name=entry.name,
                                    relpath=str(relative_path(value) / entry.name),
                                    selectable=directory,
                                    kind="directory" if directory else "unavailable",
                                )
                            )
                    except (OSError, ValueError):
                        continue
            if before != stat_identity(os.fstat(fd)):
                raise InvalidInput("Directory changed while listing.")
        finally:
            os.close(fd)
        self.model_path(value)
        entries.sort(key=lambda row: row.name)
        return DirectoryPage(
            relpath=str(relative_path(value)),
            entries=entries[offset : offset + limit],
            total=len(entries),
            offset=offset,
            limit=limit,
        )
