"""Validate input/output separation without following filesystem symlinks."""

import os
from dataclasses import dataclass
from pathlib import Path

from modelvet.core.errors import InvalidInput, PathEscape
from modelvet.core.limits import ScanLimits


def absolute_path(path: Path) -> Path:
    if ".." in path.parts or str(path).startswith("//"):
        raise PathEscape("Traversal and network paths are not accepted.")
    try:
        return path.expanduser().absolute()
    except (OSError, RuntimeError, ValueError) as exc:
        raise InvalidInput("Cannot resolve the local path.") from exc


def open_directory(path: Path, *, allow_missing: bool = False) -> int:
    """Open every component with openat/O_NOFOLLOW; caller owns the returned FD."""
    if not path.is_absolute() or ".." in path.parts:
        raise PathEscape("Expected a canonical absolute path.")
    if os.open not in os.supports_dir_fd or not hasattr(os, "O_NOFOLLOW"):
        raise InvalidInput("Secure directory access is unsupported on this platform.")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = os.open(path.anchor, flags)
    try:
        for part in path.parts[1:]:
            try:
                child = os.open(part, flags, dir_fd=fd)
            except FileNotFoundError:
                if allow_missing:
                    return fd
                raise
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def has_ancestor_identity(descriptor: int, device: int, inode: int) -> bool:
    """Resolve containment by inode, including case aliases on insensitive volumes."""
    current = os.dup(descriptor)
    try:
        while True:
            info = os.fstat(current)
            if (info.st_dev, info.st_ino) == (device, inode):
                return True
            parent = os.open("..", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current)
            parent_info = os.fstat(parent)
            if (parent_info.st_dev, parent_info.st_ino) == (info.st_dev, info.st_ino):
                os.close(parent)
                return False
            os.close(current)
            current = parent
    finally:
        os.close(current)


@dataclass(frozen=True)
class ValidatedInput:
    artifact_dir: Path
    output_dir: Path
    limits: ScanLimits
    root_device: int
    root_inode: int


class InputGate:
    def validate(
        self, artifact_dir: Path, output_dir: Path | None, limits: ScanLimits
    ) -> ValidatedInput:
        artifact = absolute_path(artifact_dir)
        output = absolute_path(output_dir or Path.home() / ".local/state/modelvet/reports")
        if output.is_relative_to(artifact):
            raise PathEscape("Reports must be outside the artifact directory.")
        try:
            fd = open_directory(artifact)
            try:
                root = os.fstat(fd)
            finally:
                os.close(fd)
            fd = open_directory(output, allow_missing=True)
            try:
                if has_ancestor_identity(fd, root.st_dev, root.st_ino):
                    raise PathEscape("Reports must be outside the artifact directory identity.")
            finally:
                os.close(fd)
        except (OSError, ValueError) as exc:
            raise InvalidInput("Input/output path is missing, unreadable or unsafe.") from exc
        return ValidatedInput(artifact, output, limits, root.st_dev, root.st_ino)
