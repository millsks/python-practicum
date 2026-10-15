"""Milestone 4: the keyword search index."""

from library import Book, Library, SearchIndex
from library.search import tokenize


def hobbit() -> Book:
    return Book("9780261102217", "The Hobbit", ("J. R. R. Tolkien",), 1937)


def lotr() -> Book:
    return Book("9780547928227", "The Fellowship of the Ring", ("J. R. R. Tolkien",), 1954)


def pride() -> Book:
    return Book("9780141439518", "Pride and Prejudice", ("Jane Austen",), 1813)


def make_index() -> SearchIndex:
    index = SearchIndex()
    for book in (hobbit(), lotr(), pride()):
        index.add(book)
    return index


def test_tokenize_lowercases_and_drops_punctuation():
    assert tokenize("The Hobbit, or There-and-Back!") == ["the", "hobbit", "or", "there", "and", "back"]


def test_search_by_author_returns_sorted_titles():
    titles = [b.title for b in make_index().search("tolkien")]
    assert titles == ["The Fellowship of the Ring", "The Hobbit"], "results are sorted by title"


def test_search_requires_every_word():
    assert make_index().search("tolkien hobbit") == [hobbit()], "all query words must match"
    assert make_index().search("tolkien prejudice") == []


def test_search_is_case_insensitive_and_empty_query_is_empty():
    assert make_index().search("pride()") == [pride()]
    assert make_index().search("  ,, ") == []


def test_len_contains_and_remove():
    index = make_index()
    assert len(index) == 3 and hobbit().isbn in index
    index.remove(hobbit().isbn)
    index.remove("unknown")
    assert len(index) == 2 and hobbit().isbn not in index
    assert index.search("hobbit") == [], "removed books disappear from results"


def test_re_adding_replaces_old_words():
    index = make_index()
    index.add(Book(hobbit().isbn, "There and Back Again", ("Bilbo Baggins",), 1937))
    assert index.search("hobbit") == [], "old title words are gone"
    assert [b.title for b in index.search("bilbo")] == ["There and Back Again"]


def test_library_search_uses_index():
    lib = Library()
    lib.add_book(pride())
    lib.add_book(hobbit())
    assert lib.search("austen") == [pride()]
