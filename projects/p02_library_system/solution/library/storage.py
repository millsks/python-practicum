"""Save a library to JSON and load it back."""

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
    return {
        "version": FORMAT_VERSION,
        "books": [
            {"isbn": b.isbn, "title": b.title, "authors": list(b.authors), "year": b.year} for b in library.books
        ],
        "copies": [
            {"copy_id": c.copy_id, "isbn": c.isbn, "status": c.status.value, "reserved_for": c.reserved_for}
            for c in library.copies
        ],
        "members": [
            {
                "member_id": m.member_id,
                "name": m.name,
                "tier": m.tier.label,
                "email": m.email,
                "fines_cents": m.fines_cents,
            }
            for m in library.members
        ],
        "loans": [
            {
                "loan_id": ln.loan_id,
                "copy_id": ln.copy_id,
                "member_id": ln.member_id,
                "borrowed_on": ln.borrowed_on.isoformat(),
                "due_on": ln.due_on.isoformat(),
                "returned_on": ln.returned_on.isoformat() if ln.returned_on else None,
            }
            for ln in library.loans
        ],
        "holds": library.holds,
    }


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
    if data.get("version") != FORMAT_VERSION:
        raise PersistenceError(f"unsupported format version {data.get('version')!r}")
    try:
        return Library.from_records(
            books=[Book(b["isbn"], b["title"], tuple(b["authors"]), int(b["year"])) for b in data["books"]],
            copies=[Copy(c["copy_id"], c["isbn"], CopyStatus(c["status"]), c["reserved_for"]) for c in data["copies"]],
            members=[
                Member(m["member_id"], m["name"], MemberTier.from_label(m["tier"]), m["email"], int(m["fines_cents"]))
                for m in data["members"]
            ],
            loans=[
                Loan(
                    ln["loan_id"],
                    ln["copy_id"],
                    ln["member_id"],
                    date.fromisoformat(ln["borrowed_on"]),
                    date.fromisoformat(ln["due_on"]),
                    date.fromisoformat(ln["returned_on"]) if ln["returned_on"] else None,
                )
                for ln in data["loans"]
            ],
            holds=dict(data["holds"]),
            clock=clock,
            notifier=notifier,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise PersistenceError(f"malformed library data: {exc}") from exc


def save_library(library: Library, path: Path) -> None:
    """Write a library to a JSON file, creating parent directories.

    Args:
        library: The library to save.
        path: Destination file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(library_to_dict(library), indent=2, sort_keys=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text + "\n", encoding="utf-8")
    tmp.replace(path)


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
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PersistenceError(f"no saved library at {path}") from exc
    except json.JSONDecodeError as exc:
        raise PersistenceError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise PersistenceError(f"{path} does not contain a JSON object")
    return library_from_dict(data, clock=clock, notifier=notifier)
