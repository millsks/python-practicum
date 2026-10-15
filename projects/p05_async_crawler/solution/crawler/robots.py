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
        parser = RobotFileParser()
        parser.parse(text.splitlines())
        return cls(user_agent, parser)

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
        if response is None or response.status != 200:
            return cls.allow_all(user_agent)
        return cls.from_text(response.body, user_agent)

    @classmethod
    def allow_all(cls, user_agent: str) -> RobotsPolicy:
        """Return a policy that permits every URL.

        Args:
            user_agent: Agent name (kept for reporting).

        Returns:
            The permissive policy.
        """
        return cls(user_agent, None)

    def allowed(self, url: str) -> bool:
        """Report whether ``url`` may be fetched.

        Args:
            url: Absolute URL.

        Returns:
            ``True`` when the rules allow the URL.
        """
        return True if self.parser is None else self.parser.can_fetch(self.user_agent, url)

    def crawl_delay(self) -> float:
        """Return the ``Crawl-delay`` for this agent, or ``0.0`` when none is set.

        Returns:
            Seconds to wait between requests.
        """
        if self.parser is None:
            return 0.0
        delay = self.parser.crawl_delay(self.user_agent)
        return float(delay) if delay is not None else 0.0
