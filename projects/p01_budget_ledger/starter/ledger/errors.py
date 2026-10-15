"""The single exception type the ledger raises for bad input."""


class LedgerError(Exception):
    """Raised when input files, rules, or arguments cannot be used.

    Every problem the ledger detects in user-supplied data is reported as a ``LedgerError`` (or a subclass), so
    callers such as the CLI need to catch only this one type. Messages always say where the problem is.
    """
