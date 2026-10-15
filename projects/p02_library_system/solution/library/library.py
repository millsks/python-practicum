"""The :class:`Library` service: catalog, members, loans, holds, fines, and search."""

from collections import deque
from collections.abc import Iterable, Mapping
from typing import Self

from library.clock import Clock, SystemClock
from library.errors import (
    DuplicateError,
    HoldError,
    LoanLimitError,
    NoCopiesAvailableError,
    NotFoundError,
    OutstandingFinesError,
)
from library.isbn import validate_isbn
from library.models import Book, Copy, CopyStatus, Loan, Member, due_date
from library.notify import InMemoryNotifier, Notifier
from library.search import SearchIndex


class Library:
    """A small library's circulation system.

    Args:
        clock: Source of today's date; defaults to the real calendar.
        notifier: Delivers messages to members; defaults to an :class:`InMemoryNotifier`.
    """

    def __init__(self, *, clock: Clock | None = None, notifier: Notifier | None = None) -> None:
        """Create an empty library."""
        self.clock: Clock = clock if clock is not None else SystemClock()
        self.notifier: Notifier = notifier if notifier is not None else InMemoryNotifier()
        self._books: dict[str, Book] = {}
        self._copies: dict[str, Copy] = {}
        self._members: dict[str, Member] = {}
        self._loans: dict[str, Loan] = {}
        self._holds: dict[str, deque[str]] = {}
        self._index = SearchIndex()
        self._next_copy = 1
        self._next_loan = 1

    @classmethod
    def from_records(
        cls,
        *,
        books: Iterable[Book],
        copies: Iterable[Copy],
        members: Iterable[Member],
        loans: Iterable[Loan],
        holds: Mapping[str, Iterable[str]],
        clock: Clock | None = None,
        notifier: Notifier | None = None,
    ) -> Self:
        """Rebuild a library from previously saved records.

        Args:
            books: Catalog entries.
            copies: Physical copies, with their current status.
            members: Card holders, with their fines.
            loans: Open and closed loans.
            holds: Waiting lists keyed by ISBN, first in line first.
            clock: Source of today's date.
            notifier: Delivers messages to members.

        Returns:
            A library in the saved state; new ids continue after the highest saved ones.
        """
        lib = cls(clock=clock, notifier=notifier)
        for book in books:
            lib._books[book.isbn] = book
            lib._index.add(book)
        for copy in copies:
            lib._copies[copy.copy_id] = copy
        for member in members:
            lib._members[member.member_id] = member
        for loan in loans:
            lib._loans[loan.loan_id] = loan
        for isbn, queue in holds.items():
            lib._holds[isbn] = deque(queue)
        lib._next_copy = 1 + max((int(c[1:]) for c in lib._copies), default=0)
        lib._next_loan = 1 + max((int(n[1:]) for n in lib._loans), default=0)
        return lib

    # ---- catalog -------------------------------------------------------------------------------------------

    def add_book(self, book: Book, copies: int = 1) -> list[Copy]:
        """Add a new title with some physical copies.

        Args:
            book: The title to catalog.
            copies: How many copies to create; at least one.

        Returns:
            The new copies.

        Raises:
            DuplicateError: If the ISBN is already cataloged.
            ValueError: If ``copies`` is less than one.
        """
        if book.isbn in self._books:
            raise DuplicateError(f"book {book.isbn} is already in the catalog")
        if copies < 1:
            raise ValueError("a new book needs at least one copy")
        self._books[book.isbn] = book
        self._index.add(book)
        return self.add_copies(book.isbn, copies)

    def add_copies(self, isbn: str, count: int) -> list[Copy]:
        """Add more copies of a cataloged title; each one first serves the hold queue.

        Args:
            isbn: ISBN of a cataloged book.
            count: How many copies to add.

        Returns:
            The new copies.
        """
        book = self.get_book(isbn)
        new: list[Copy] = []
        for _ in range(count):
            copy = Copy(copy_id=f"C{self._next_copy:05d}", isbn=book.isbn)
            self._next_copy += 1
            self._copies[copy.copy_id] = copy
            self._shelve(copy)
            new.append(copy)
        return new

    def get_book(self, isbn: str) -> Book:
        """Look up a title.

        Args:
            isbn: Any valid form of the ISBN.

        Returns:
            The book.

        Raises:
            NotFoundError: If the book is not cataloged.
        """
        try:
            return self._books[validate_isbn(isbn)]
        except KeyError:
            raise NotFoundError(f"no book with ISBN {isbn}") from None

    def get_copy(self, copy_id: str) -> Copy:
        """Look up a physical copy.

        Args:
            copy_id: The copy's barcode.

        Returns:
            The copy.

        Raises:
            NotFoundError: If no copy has that id.
        """
        try:
            return self._copies[copy_id]
        except KeyError:
            raise NotFoundError(f"no copy {copy_id}") from None

    def copies_of(self, isbn: str) -> list[Copy]:
        """Return every copy of a title.

        Args:
            isbn: ISBN of a cataloged book.

        Returns:
            Copies ordered by id.
        """
        canonical = self.get_book(isbn).isbn
        return [c for c in self._copies.values() if c.isbn == canonical]

    def available_copies(self, isbn: str) -> int:
        """Count copies anyone may borrow now.

        Args:
            isbn: ISBN of a cataloged book.

        Returns:
            The number of available copies.
        """
        return sum(1 for c in self.copies_of(isbn) if c.is_available)

    def search(self, query: str) -> list[Book]:
        """Keyword search over titles and authors.

        Args:
            query: Words that must all appear.

        Returns:
            Matching books sorted by title.
        """
        return self._index.search(query)

    @property
    def books(self) -> list[Book]:
        """Every cataloged title."""
        return list(self._books.values())

    @property
    def copies(self) -> list[Copy]:
        """Every physical copy."""
        return list(self._copies.values())

    @property
    def members(self) -> list[Member]:
        """Every registered member."""
        return list(self._members.values())

    @property
    def loans(self) -> list[Loan]:
        """Every loan, open and closed."""
        return list(self._loans.values())

    @property
    def holds(self) -> dict[str, list[str]]:
        """Waiting lists keyed by ISBN, first in line first."""
        return {isbn: list(queue) for isbn, queue in self._holds.items() if queue}

    def __len__(self) -> int:
        """Return the number of cataloged titles."""
        return len(self._books)

    def __contains__(self, isbn: object) -> bool:
        """Return whether an ISBN (in any valid form) is cataloged."""
        if not isinstance(isbn, str):
            return False
        try:
            return validate_isbn(isbn) in self._books
        except ValueError:
            return False

    # ---- members -------------------------------------------------------------------------------------------

    def register_member(self, member: Member) -> Member:
        """Register a new card holder.

        Args:
            member: The new member.

        Returns:
            The same member, for chaining.

        Raises:
            DuplicateError: If the member id is taken.
        """
        if member.member_id in self._members:
            raise DuplicateError(f"member {member.member_id} already exists")
        self._members[member.member_id] = member
        return member

    def get_member(self, member_id: str) -> Member:
        """Look up a member.

        Args:
            member_id: Card number.

        Returns:
            The member.

        Raises:
            NotFoundError: If nobody has that card number.
        """
        try:
            return self._members[member_id]
        except KeyError:
            raise NotFoundError(f"no member {member_id}") from None

    def loans_for(self, member_id: str) -> list[Loan]:
        """Return a member's open loans.

        Args:
            member_id: Card number.

        Returns:
            Open loans ordered by due date.
        """
        self.get_member(member_id)
        return sorted((ln for ln in self._loans.values() if ln.member_id == member_id and ln.is_open), key=_by_due)

    def pay_fine(self, member_id: str, cents: int) -> int:
        """Record a fine payment.

        Args:
            member_id: Card number.
            cents: Amount paid; positive and no more than the balance.

        Returns:
            The remaining balance in cents.

        Raises:
            ValueError: If the amount is not positive or exceeds the balance.
        """
        member = self.get_member(member_id)
        if cents <= 0 or cents > member.fines_cents:
            raise ValueError(f"payment must be between 1 and {member.fines_cents} cents")
        member.fines_cents -= cents
        return member.fines_cents

    # ---- circulation ---------------------------------------------------------------------------------------

    def checkout(self, member_id: str, isbn: str) -> Loan:
        """Lend a copy of a title to a member.

        A copy waiting on the hold shelf for this member is used first; otherwise any available copy.

        Args:
            member_id: Borrower's card number.
            isbn: Title to borrow.

        Returns:
            The new loan, due after the member's tier loan period.

        Raises:
            OutstandingFinesError: If the member owes too much.
            LoanLimitError: If the member is at their tier's limit.
            NoCopiesAvailableError: If no copy is free for this member.
        """
        member = self.get_member(member_id)
        book = self.get_book(isbn)
        if member.is_blocked:
            raise OutstandingFinesError(f"{member.name} owes {member.fines_cents} cents")
        if len(self.loans_for(member_id)) >= member.tier.loan_limit:
            raise LoanLimitError(f"{member.name} has reached the {member.tier.label} limit")
        copy = self._copy_for(member_id, book.isbn)
        if copy is None:
            raise NoCopiesAvailableError(f"no copy of {book.title!r} is available")
        today = self.clock.today()
        loan = Loan(f"L{self._next_loan:05d}", copy.copy_id, member_id, today, due_date(today, member.tier))
        self._next_loan += 1
        self._loans[loan.loan_id] = loan
        copy.status, copy.reserved_for = CopyStatus.ON_LOAN, None
        return loan

    def return_copy(self, copy_id: str) -> Loan:
        """Check a copy back in, charge any late fine, and serve the hold queue.

        Args:
            copy_id: Barcode of the returned copy.

        Returns:
            The closed loan.

        Raises:
            NotFoundError: If the copy has no open loan.
        """
        copy = self.get_copy(copy_id)
        loan = next((ln for ln in self._loans.values() if ln.copy_id == copy_id and ln.is_open), None)
        if loan is None:
            raise NotFoundError(f"copy {copy_id} is not on loan")
        loan.returned_on = self.clock.today()
        fine = loan.fine_cents(loan.returned_on)
        if fine:
            member = self.get_member(loan.member_id)
            member.fines_cents += fine
            self.notifier.send(member, "Late return fine", f"A fine of {fine} cents was added to your account.")
        self._shelve(copy)
        return loan

    def overdue_loans(self) -> list[Loan]:
        """Return every open loan past its due date.

        Returns:
            Overdue loans, most overdue first.
        """
        today = self.clock.today()
        return sorted((ln for ln in self._loans.values() if ln.is_overdue(today)), key=_by_due)

    def send_overdue_notices(self) -> int:
        """Notify every member with an overdue loan, once per loan.

        Returns:
            How many notices were sent.
        """
        overdue = self.overdue_loans()
        for loan in overdue:
            book = self._books[self._copies[loan.copy_id].isbn]
            self.notifier.send(
                self.get_member(loan.member_id), "Overdue", f"{book.title!r} was due on {loan.due_on.isoformat()}."
            )
        return len(overdue)

    # ---- holds ---------------------------------------------------------------------------------------------

    def place_hold(self, member_id: str, isbn: str) -> int:
        """Join the waiting list for a title with no free copies.

        Args:
            member_id: Card number.
            isbn: Title to wait for.

        Returns:
            The member's 1-based position in the queue.

        Raises:
            HoldError: If a copy is available, the member already has a hold, or already has the title on loan.
        """
        self.get_member(member_id)
        book = self.get_book(isbn)
        if self.available_copies(book.isbn):
            raise HoldError(f"{book.title!r} is on the shelf; borrow it instead")
        queue = self._holds.setdefault(book.isbn, deque())
        if member_id in queue or any(c.reserved_for == member_id for c in self.copies_of(book.isbn)):
            raise HoldError(f"{member_id} already has a hold on {book.title!r}")
        if any(self._copies[ln.copy_id].isbn == book.isbn for ln in self.loans_for(member_id)):
            raise HoldError(f"{member_id} already has {book.title!r} on loan")
        queue.append(member_id)
        return len(queue)

    def cancel_hold(self, member_id: str, isbn: str) -> None:
        """Leave a waiting list, releasing any copy held on the shelf for the member.

        Args:
            member_id: Card number.
            isbn: Title of the hold.

        Raises:
            HoldError: If the member has no hold on the title.
        """
        book = self.get_book(isbn)
        queue = self._holds.get(book.isbn, deque())
        if member_id in queue:
            queue.remove(member_id)
            return
        for copy in self.copies_of(book.isbn):
            if copy.reserved_for == member_id:
                self._shelve(copy)
                return
        raise HoldError(f"{member_id} has no hold on {book.title!r}")

    def holds_for(self, isbn: str) -> list[str]:
        """Return the waiting list for a title.

        Args:
            isbn: Title to inspect.

        Returns:
            Member ids, first in line first.
        """
        return list(self._holds.get(self.get_book(isbn).isbn, ()))

    # ---- helpers -------------------------------------------------------------------------------------------

    def _copy_for(self, member_id: str, isbn: str) -> Copy | None:
        copies = self.copies_of(isbn)
        reserved = next((c for c in copies if c.reserved_for == member_id), None)
        return reserved or next((c for c in copies if c.is_available), None)

    def _shelve(self, copy: Copy) -> None:
        """Put a copy back: onto the hold shelf for the next member in line, or onto the open shelf."""
        queue = self._holds.get(copy.isbn)
        if queue:
            member = self.get_member(queue.popleft())
            copy.status, copy.reserved_for = CopyStatus.ON_HOLD_SHELF, member.member_id
            title = self._books[copy.isbn].title
            self.notifier.send(member, "Hold ready", f"{title!r} is waiting for you at the front desk.")
        else:
            copy.status, copy.reserved_for = CopyStatus.AVAILABLE, None


def _by_due(loan: Loan) -> tuple[str, str]:
    return loan.due_on.isoformat(), loan.loan_id
