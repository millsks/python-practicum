"""Exception hierarchy for the library system.

Every error the package raises derives from :class:`LibraryError`, so callers can catch one type at the boundary.
"""


class LibraryError(Exception):
    """Base class for every error raised by the library package."""


class InvalidISBNError(LibraryError, ValueError):
    """Raised when a string is not a valid ISBN-10 or ISBN-13."""


class NotFoundError(LibraryError, LookupError):
    """Raised when a book, copy, member, or loan does not exist."""


class DuplicateError(LibraryError):
    """Raised when adding something whose identifier is already registered."""


class NoCopiesAvailableError(LibraryError):
    """Raised when every copy of a title is out on loan or reserved for someone else."""


class LoanLimitError(LibraryError):
    """Raised when a member already has as many loans as their tier allows."""


class OutstandingFinesError(LibraryError):
    """Raised when a member's unpaid fines block borrowing."""


class HoldError(LibraryError):
    """Raised for an invalid hold request, such as a duplicate hold."""


class PersistenceError(LibraryError):
    """Raised when a saved library file cannot be read or has the wrong shape."""
