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
    return _WORD.findall(text.casefold())


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
        if book.isbn in self._books:
            self.remove(book.isbn)
        self._books[book.isbn] = book
        for word in tokenize(book.title + " " + " ".join(book.authors)):
            self._postings[word].add(book.isbn)

    def remove(self, isbn: str) -> None:
        """Remove a book from the index; unknown ISBNs are ignored.

        Args:
            isbn: Canonical ISBN of the book.
        """
        book = self._books.pop(isbn, None)
        if book is None:
            return
        for word in tokenize(book.title + " " + " ".join(book.authors)):
            isbns = self._postings.get(word)
            if isbns is not None:
                isbns.discard(isbn)
                if not isbns:
                    del self._postings[word]

    def search(self, query: str) -> list[Book]:
        """Find books containing every word in ``query``.

        Args:
            query: Keywords such as ``"tolkien hobbit"``; matching is case-insensitive.

        Returns:
            Matching books sorted by title, then year. An empty query returns an empty list.
        """
        words = tokenize(query)
        if not words:
            return []
        matches = set.intersection(*(self._postings.get(word, set()) for word in words))
        return sorted((self._books[isbn] for isbn in matches), key=lambda b: (b.title.casefold(), b.year))

    def __len__(self) -> int:
        """Return the number of indexed books."""
        return len(self._books)

    def __contains__(self, isbn: object) -> bool:
        """Return whether an ISBN is indexed."""
        return isbn in self._books
