"""Milestone 5: the DAG runner and retries."""

from graphlib import CycleError

import pytest
from etl.dag import DAG, TaskFailedError, retry


def test_order_respects_dependencies() -> None:
    dag = DAG()
    dag.add("load", lambda r: None, deps=("transform",))
    dag.add("extract", lambda r: None)
    dag.add("transform", lambda r: None, deps=("extract",))
    order = dag.order()
    assert order.index("extract") < order.index("transform") < order.index("load")


def test_results_flow_downstream() -> None:
    dag = DAG()
    dag.add("a", lambda r: 2)
    dag.add("b", lambda r: r["a"] * 10, deps=("a",))
    assert dag.run() == {"a": 2, "b": 20}, "each task sees upstream results by name"


def test_cycle_detected() -> None:
    dag = DAG()
    dag.add("a", lambda r: None, deps=("b",))
    dag.add("b", lambda r: None, deps=("a",))
    with pytest.raises(CycleError):
        dag.order()


def test_unknown_dependency_and_duplicate_name() -> None:
    dag = DAG()
    dag.add("a", lambda r: None, deps=("ghost",))
    with pytest.raises(ValueError):
        dag.order()
    with pytest.raises(ValueError):
        dag.add("a", lambda r: None)


def test_task_retries_then_succeeds() -> None:
    calls = {"n": 0}

    def flaky(_: dict) -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("blip")
        return "ok"

    dag = DAG()
    dag.add("flaky", flaky, retries=2)
    assert dag.run() == {"flaky": "ok"} and calls["n"] == 3, "two failures then success within retries=2"


def test_task_failure_stops_downstream() -> None:
    ran: list[str] = []
    dag = DAG()
    dag.add("bad", lambda r: 1 / 0, retries=1)
    dag.add("after", lambda r: ran.append("after"), deps=("bad",))
    with pytest.raises(TaskFailedError) as info:
        dag.run()
    assert info.value.task == "bad" and info.value.attempts == 2, "1 attempt + 1 retry"
    assert isinstance(info.value.__cause__, ZeroDivisionError), "the original error is chained"
    assert ran == [], "downstream tasks never run after a failure"


def test_retry_decorator() -> None:
    calls = {"n": 0}

    @retry(2, exceptions=(TimeoutError,))
    def fetch() -> int:
        calls["n"] += 1
        if calls["n"] == 1:
            raise TimeoutError
        return 42

    assert fetch() == 42 and calls["n"] == 2
    assert fetch.__name__ == "fetch", "functools.wraps preserves the name"


def test_retry_decorator_gives_up_and_ignores_other_errors() -> None:
    @retry(1, exceptions=(TimeoutError,))
    def always_timeout() -> None:
        raise TimeoutError("slow")

    with pytest.raises(TimeoutError):
        always_timeout()

    calls = {"n": 0}

    @retry(3, exceptions=(TimeoutError,))
    def wrong_kind() -> None:
        calls["n"] += 1
        raise KeyError("bug")

    with pytest.raises(KeyError):
        wrong_kind()
    assert calls["n"] == 1, "non-retryable errors propagate immediately"
