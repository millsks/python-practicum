"""Notifications sent to members, behind a Protocol so tests never send real email."""

from dataclasses import dataclass
from typing import Protocol

from library.models import Member


@dataclass(frozen=True, slots=True)
class Notification:
    """A message delivered to a member.

    Attributes:
        member_id: Recipient.
        subject: Short subject line.
        body: Message text.
    """

    member_id: str
    subject: str
    body: str


class Notifier(Protocol):
    """Anything that can deliver a message to a member."""

    def send(self, member: Member, subject: str, body: str) -> None:
        """Deliver a message.

        Args:
            member: Recipient.
            subject: Short subject line.
            body: Message text.
        """
        ...


class InMemoryNotifier:
    """A notifier that records messages in a list, for tests and demos."""

    def __init__(self) -> None:
        """Start with no messages."""
        self.sent: list[Notification] = []

    def send(self, member: Member, subject: str, body: str) -> None:
        """Record a message instead of delivering it.

        Args:
            member: Recipient.
            subject: Short subject line.
            body: Message text.
        """
        self.sent.append(Notification(member.member_id, subject, body))

    def for_member(self, member_id: str) -> list[Notification]:
        """Return the messages sent to one member.

        Args:
            member_id: Recipient to filter by.

        Returns:
            Messages in the order they were sent.
        """
        return [n for n in self.sent if n.member_id == member_id]

    def __len__(self) -> int:
        """Return how many messages were sent."""
        return len(self.sent)
