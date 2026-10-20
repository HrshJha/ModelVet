"""Errors carry controlled messages, never arbitrary artifact bytes or paths."""


class InvalidInput(Exception):
    """Input cannot safely enter an assessment."""


class BudgetExceeded(InvalidInput):
    """A configured resource budget was exceeded."""


class PathEscape(InvalidInput):
    """A path crosses a prohibited boundary."""


class SnapshotChanged(InvalidInput):
    """Filesystem identity changed during or after ingestion."""


class IOFailure(InvalidInput):
    """A bounded input operation could not complete."""
