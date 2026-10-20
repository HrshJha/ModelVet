"""Provisional ceilings: requests may reduce, but cannot raise, these limits."""

from dataclasses import dataclass, fields

from modelvet.core.errors import BudgetExceeded

MIB = 1024 * 1024


@dataclass(frozen=True)
class ScanLimits:
    max_files: int = 10_000
    max_file_bytes: int = 1024 * MIB
    max_total_bytes: int = 2048 * MIB
    max_metadata_bytes: int = 16 * MIB
    timeout_s: int = 120

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            ceiling = field.default
            if not isinstance(ceiling, int) or type(value) is not int or not 1 <= value <= ceiling:
                raise BudgetExceeded("Limits must be positive integers within reviewed ceilings.")
