"""A tiny DAG runner: tasks as functions, dependency order from graphlib, and retries."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import structlog

log = structlog.get_logger(__name__)

Results = dict[str, Any]
"""Outputs of finished tasks keyed by task name; each task receives this mapping."""


class TaskFailedError(RuntimeError):
    """Raised when a task still fails after all its retries.

    Attributes:
        task: Name of the failing task.
        attempts: How many times it ran.
    """

    def __init__(self, task: str, attempts: int) -> None:
        """Create the error.

        Args:
            task: Task name.
            attempts: Attempts made.
        """
        # TODO: call super().__init__ with a message; store task and attempts
        raise NotImplementedError


def retry(
    times: int, *, exceptions: tuple[type[Exception], ...] = (Exception,), delay: float = 0.0
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorate a function so it is retried on failure.

    Args:
        times: Retries after the first attempt (``times=2`` means up to three calls).
        exceptions: Exception types that trigger a retry; anything else propagates immediately.
        delay: Seconds to wait before the first retry; doubles on each further retry (exponential backoff).

    Returns:
        A decorator.
    """
    # TODO: a decorator factory; loop times + 1 attempts, re-raise on the last, sleep with doubling delay
    raise NotImplementedError


@dataclass(frozen=True, slots=True)
class Task:
    """One node in a :class:`DAG`.

    Attributes:
        name: Unique task name.
        fn: Callable receiving the results of all tasks finished so far and returning this task's result.
        deps: Names of tasks that must finish first.
        retries: Extra attempts after the first failure.
    """

    name: str
    fn: Callable[[Results], Any]
    deps: tuple[str, ...] = ()
    retries: int = 0


@dataclass(slots=True)
class DAG:
    """A directed acyclic graph of tasks.

    Attributes:
        tasks: Registered tasks keyed by name.
    """

    tasks: dict[str, Task] = field(default_factory=dict)

    def add(self, name: str, fn: Callable[[Results], Any], deps: tuple[str, ...] = (), retries: int = 0) -> Task:
        """Register a task.

        Args:
            name: Unique task name.
            fn: Task callable.
            deps: Upstream task names.
            retries: Extra attempts on failure.

        Returns:
            The new task.

        Raises:
            ValueError: If the name is already used.
        """
        # TODO: reject duplicate names; store Task(name, fn, tuple(deps), retries)
        raise NotImplementedError

    def order(self) -> list[str]:
        """Return a valid execution order.

        Returns:
            Task names, dependencies first.

        Raises:
            ValueError: If a task depends on an unregistered task.
            graphlib.CycleError: If the dependencies contain a cycle.
        """
        # TODO: check unknown deps, then graphlib.TopologicalSorter(...).static_order()
        raise NotImplementedError

    def run(self) -> Results:
        """Run every task once in dependency order, retrying failures.

        Returns:
            Each task's return value keyed by name.

        Raises:
            TaskFailedError: If a task fails after its retries; downstream tasks do not run.
        """
        # TODO: for each name in order(): call task.fn(results) up to retries + 1 times; raise TaskFailedError from the last error
        raise NotImplementedError
