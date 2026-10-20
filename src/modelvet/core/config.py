"""Bounded, data-only TOML policy loading with no ambient environment overrides."""

import json
import os
import stat
import tomllib
from importlib.resources import files
from pathlib import Path

from pydantic import ValidationError

from modelvet.core.errors import InvalidInput
from modelvet.inventory.discover import stat_identity
from modelvet.inventory.gate import absolute_path, open_directory
from modelvet.policies.models import Policy

MAX_POLICY_BYTES = 64 * 1024
MAX_POLICY_NODES = 4096
MAX_POLICY_DEPTH = 16


class PolicyValidator:
    def parse(self, toml_bytes: bytes) -> Policy:
        if not toml_bytes or len(toml_bytes) > MAX_POLICY_BYTES:
            raise InvalidInput("Policy is empty or exceeds the 64 KiB limit.")
        try:
            data = tomllib.loads(toml_bytes.decode("utf-8", errors="strict"))
            pending: list[tuple[object, int]] = [(data, 0)]
            count = 0
            while pending:
                value, depth = pending.pop()
                count += 1
                if count > MAX_POLICY_NODES or depth > MAX_POLICY_DEPTH:
                    raise InvalidInput("Policy exceeds structural limits.")
                if isinstance(value, dict):
                    pending.extend((v, depth + 1) for v in value.values())
                elif isinstance(value, list):
                    pending.extend((v, depth + 1) for v in value)
            # JSON-mode validation preserves strict scalar types while accepting
            # TOML arrays as immutable tuples. Dates/nonfinite numbers are refused.
            encoded = json.dumps(data, allow_nan=False, ensure_ascii=True)
            return Policy.model_validate_json(encoded)
        except (ValueError, TypeError, RecursionError, ValidationError) as exc:
            # Parser/validation errors may embed arbitrary policy text or paths.
            raise InvalidInput("Invalid policy TOML or unsupported v1 rule/schema.") from exc


def load_policy(path: Path | None = None) -> Policy:
    """Explicit selection replaces the default; invalid selection never falls back."""
    if path is None:
        raw = files("modelvet.policies").joinpath("default.toml").read_bytes()
        return PolicyValidator().parse(raw)
    selected = absolute_path(path)
    try:
        parent_fd = open_directory(selected.parent)
    except OSError as exc:
        raise InvalidInput("Cannot safely read the selected policy directory.") from exc
    try:
        descriptor = os.open(
            selected.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
            dir_fd=parent_fd,
        )
        with os.fdopen(descriptor, "rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                raise InvalidInput("Policy must be a regular file without hardlinks.")
            if before.st_size > MAX_POLICY_BYTES:
                raise InvalidInput("Policy exceeds the 64 KiB limit.")
            raw = stream.read(MAX_POLICY_BYTES + 1)
            after = os.fstat(stream.fileno())
            if stat_identity(before) != stat_identity(after) or len(raw) != before.st_size:
                raise InvalidInput("Policy changed while reading.")
    except OSError as exc:
        raise InvalidInput("Cannot safely read the selected policy file.") from exc
    finally:
        os.close(parent_fd)
    return PolicyValidator().parse(raw)
