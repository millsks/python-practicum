"""Save a library to JSON and load it back."""

# The imports below are the ones your implementation will need.
# ruff: noqa: F401

import json
from datetime import date
from pathlib import Path
from typing import Any

from library.clock import Clock
from library.errors import PersistenceError
from library.library import Library
from library.models import Book, Copy, CopyStatus, Loan, Member, MemberTier
from library.notify import Notifier

FORMAT_VERSION = 1


def library_to_dict(library: Library) -> dict[str, Any]:
    """Convert a library to JSON-compatible data.

    Args:
        library: The library to serialize.

    Returns:
        A dictionary of plain lists, dicts, strings, and numbers. Dates become ISO strings.
    """
    # TODO: Build plain dicts/lists; enums become their value/label and dates become isoformat() strings. Include a 'version' key.
    raise NotImplementedError


def library_from_dict(data: dict[str, Any], *, clock: Clock | None = None, notifier: Notifier | None = None) -> Library:
    """Rebuild a library from :func:`library_to_dict` output.

    Args:
        data: Previously serialized data.
        clock: Clock for the rebuilt library.
        notifier: Notifier for the rebuilt library.

    Returns:
        The rebuilt library.

    Raises:
        PersistenceError: If the data has an unknown version or a missing or malformed field.
    """
    # TODO: Check the version; rebuild each record; wrap KeyError/TypeError/ValueError in PersistenceError.
    raise NotImplementedError


def save_library(library: Library, path: Path) -> None:
    """Write a library to a JSON file, creating parent directories.

    Args:
        library: The library to save.
        path: Destination file.
    """
    # TODO: mkdir the parent, json.dumps with indent=2, write to a temporary file, then replace() the target.
    raise NotImplementedError


def load_library(path: Path, *, clock: Clock | None = None, notifier: Notifier | None = None) -> Library:
    """Read a library saved by :func:`save_library`.

    Args:
        path: The JSON file.
        clock: Clock for the loaded library.
        notifier: Notifier for the loaded library.

    Returns:
        The loaded library.

    Raises:
        PersistenceError: If the file is missing, is not JSON, or has the wrong shape.
    """
    # TODO: Read and parse; turn FileNotFoundError and JSONDecodeError into PersistenceError; require a dict.
    raise NotImplementedError
