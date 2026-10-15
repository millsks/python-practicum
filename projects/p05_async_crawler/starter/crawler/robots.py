"""``robots.txt`` rules via :mod:`urllib.robotparser`."""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.robotparser import RobotFileParser

from crawler.models import Response


@dataclass
class RobotsPolicy:
    """Crawl permissions for one site.

    Attributes:
        user_agent: Agent name matched against ``User-agent`` lines.
        parser: The parsed rules, or ``None`` to allow everything.
    """

    user_agent: str
    parser: RobotFileParser | None = field(default=None, repr=False)

    @classmethod
    def from_text(cls, text: str, user_agent: str) -> RobotsPolicy:
        """Build a policy from the body of a ``robots.txt`` file.

        Args:
            text: File contents.
            user_agent: Agent name to match.

        Returns:
            The policy.
        """
        # TODO: RobotFileParser().parse(lines) accepts the file as a list of lines.
        raise NotImplementedError

    @classmethod
    def from_response(cls, response: Response | None, user_agent: str) -> RobotsPolicy:
        """Build a policy from a fetched ``robots.txt`` response.

        A missing file (any non-200 answer, or no response at all) means the site sets no rules.

        Args:
            response: The response, or ``None`` when fetching failed.
            user_agent: Agent name to match.

        Returns:
            The policy.
        """
        # TODO: Only a 200 response has rules; anything else (or None) allows all.
        raise NotImplementedError

    @classmethod
    def allow_all(cls, user_agent: str) -> RobotsPolicy:
        """Return a policy that permits every URL.

        Args:
            user_agent: Agent name (kept for reporting).

        Returns:
            The permissive policy.
        """
        # TODO: A policy whose parser is None allows everything.
        raise NotImplementedError

    def allowed(self, url: str) -> bool:
        """Report whether ``url`` may be fetched.

        Args:
            url: Absolute URL.

        Returns:
            ``True`` when the rules allow the URL.
        """
        # TODO: Use parser.can_fetch(user_agent, url).
        raise NotImplementedError

    def crawl_delay(self) -> float:
        """Return the ``Crawl-delay`` for this agent, or ``0.0`` when none is set.

        Returns:
            Seconds to wait between requests.
        """
        # TODO: parser.crawl_delay(agent) returns None when unset.
        raise NotImplementedError
