"""A tiny DAG runner: tasks as functions, dependency order from graphlib, and retries."""

import functools
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from graphlib import TopologicalSorter
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
        super().__init__(f"task {task!r} failed after {attempts} attempt(s)")
        self.task = task
        self.attempts = attempts


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

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            wait = delay
            for attempt in range(times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if attempt == times:
                        raise
                    log.warning("retrying", func=func.__name__, attempt=attempt + 1, error=str(exc))
                    if wait:
                        time.sleep(wait)
                        wait *= 2
            raise AssertionError("unreachable")  # pragma: no cover

        return wrapper

    return decorator


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
        if name in self.tasks:
            raise ValueError(f"duplicate task {name!r}")
        task = Task(name, fn, tuple(deps), retries)
        self.tasks[name] = task
        return task

    def order(self) -> list[str]:
        """Return a valid execution order.

        Returns:
            Task names, dependencies first.

        Raises:
            ValueError: If a task depends on an unregistered task.
            graphlib.CycleError: If the dependencies contain a cycle.
        """
        for task in self.tasks.values():
            missing = [d for d in task.deps if d not in self.tasks]
            if missing:
                raise ValueError(f"task {task.name!r} depends on unknown task(s) {missing}")
        sorter = TopologicalSorter({t.name: t.deps for t in self.tasks.values()})
        return list(sorter.static_order())

    def run(self) -> Results:
        """Run every task once in dependency order, retrying failures.

        Returns:
            Each task's return value keyed by name.

        Raises:
            TaskFailedError: If a task fails after its retries; downstream tasks do not run.
        """
        results: Results = {}
        for name in self.order():
            task = self.tasks[name]
            for attempt in range(1, task.retries + 2):
                try:
                    results[name] = task.fn(results)
                    log.info("task_succeeded", task=name, attempt=attempt)
                    break
                except Exception as exc:
                    log.warning("task_failed", task=name, attempt=attempt, error=str(exc))
                    if attempt > task.retries:
                        raise TaskFailedError(name, attempt) from exc
        return results
