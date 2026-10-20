"""Bounded JSON-as-data parsing with ambiguity and nesting rejection."""

import json
import math
from typing import Any

from modelvet.core.errors import InvalidInput


def strict_json(raw: bytes, max_bytes: int, *, max_tokens: int = 100_000) -> Any:
    if len(raw) > max_bytes:
        raise InvalidInput("JSON byte budget exceeded.")
    depth = tokens = 0
    quoted = escaped = False
    for char in raw:
        if quoted:
            if escaped:
                escaped = False
            elif char == 92:
                escaped = True
            elif char == 34:
                quoted = False
        elif char == 34:
            quoted = True
        elif char in (91, 123):
            depth += 1
            tokens += 1
        elif char in (93, 125):
            depth -= 1
        elif char in (44, 58):
            tokens += 1
        if depth < 0 or depth > 64 or tokens > max_tokens:
            raise InvalidInput("JSON nesting or token budget exceeded.")

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise InvalidInput("Duplicate JSON key.")
            result[key] = value
        return result

    def invalid_constant(value: str) -> Any:
        raise InvalidInput("Nonfinite JSON value.")

    def check(value: Any) -> None:
        if isinstance(value, str):
            value.encode("utf-8", errors="strict")
        elif isinstance(value, float) and not math.isfinite(value):
            raise InvalidInput("Nonfinite JSON number.")
        elif isinstance(value, dict):
            for key, child in value.items():
                check(key)
                check(child)
        elif isinstance(value, list):
            for child in value:
                check(child)

    try:
        value = json.loads(
            raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=invalid_constant
        )
        check(value)
        return value
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise InvalidInput("Malformed JSON data.") from exc
