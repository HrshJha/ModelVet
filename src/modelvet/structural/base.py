"""Internal inspection outcomes; wire normalization is separate."""

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class Inspection:
    check_id: str
    status: Literal["COMPLETE", "FAILED", "UNSUPPORTED"]
    reason: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    limitations: tuple[str, ...] = ()
