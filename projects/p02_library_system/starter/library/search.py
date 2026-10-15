"""An inverted index for keyword search over titles and authors."""

import re
from collections import defaultdict

from library.models import Book

_WORD = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Split text into lower-case alphanumeric words.

    Args:
        text: Any text, for example ``"The Hobbit, or There and Back Again"``.

    Returns:
        Words in order, for example ``["the", "hobbit", "or", "there", "and", "back", "again"]``.
    """
    # TODO: Use the _WORD regex on text.casefold().
    raise NotImplementedError


class SearchIndex:
    """Maps each word in a book's title and authors to the ISBNs that contain it."""

    def __init__(self) -> None:
        """Create an empty index."""
        self._postings: defaultdict[str, set[str]] = defaultdict(set)
        self._books: dict[str, Book] = {}

    def add(self, book: Book) -> None:
        """Index a book; re-adding the same ISBN replaces the old entry.

        Args:
            book: The book to index.
        """
        # TODO: Remove any old entry for the ISBN first; store the book; add its ISBN to the posting set of each title/author word.
        raise NotImplementedError

    def remove(self, isbn: str) -> None:
        """Remove a book from the index; unknown ISBNs are ignored.

        Args:
            isbn: Canonical ISBN of the book.
        """
        # TODO: Pop the book; discard its ISBN from each word's set; delete empty sets.
        raise NotImplementedError

    def search(self, query: str) -> list[Book]:
        """Find books containing every word in ``query``.

        Args:
            query: Keywords such as ``"tolkien hobbit"``; matching is case-insensitive.

        Returns:
            Matching books sorted by title, then year. An empty query returns an empty list.
        """
        # TODO: Tokenize the query; intersect the posting sets (set.intersection); sort the books by (title.casefold(), year).
        raise NotImplementedError

    def __len__(self) -> int:
        """Return the number of indexed books."""
        # TODO: Number of indexed books.
        raise NotImplementedError

    def __contains__(self, isbn: object) -> bool:
        """Return whether an ISBN is indexed."""
        # TODO: Whether the ISBN is indexed.
        raise NotImplementedError
