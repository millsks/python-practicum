import pytest

from practicum.exercises import Exercise, check_exercise

pytestmark = pytest.mark.integration


def make(solution: str, tests: str, stdin: str = "") -> Exercise:
    return Exercise("x-e1", solution, tests, stdin)


def test_passing_solution() -> None:
    exercise = make(
        "name = input()\nprint('hi', name)\ndef double(n):\n    return n * 2\n",
        "def test_double():\n    assert double(2) == 4\n"
        "def test_output():\n    assert program_output == 'hi Ada\\n'\n"
        "def test_capture():\n    assert capture_output(print, 'x') == (None, 'x\\n')\n",
        stdin="Ada\n",
    )
    assert check_exercise(exercise).ok


def test_top_level_await_is_supported() -> None:
    exercise = make(
        "import asyncio\nasync def f():\n    return 3\nvalue = await f()\n",
        "async def test_value():\n    assert value == 3\n",
    )
    assert check_exercise(exercise).ok


def test_failing_assertion_is_reported() -> None:
    result = check_exercise(make("x = 1\n", "def test_x():\n    assert x == 2, 'x should be 2'\n"))
    assert not result.ok
    assert "x should be 2" in result.detail


def test_solution_error_is_reported() -> None:
    result = check_exercise(make("raise ValueError('nope')\n", "def test_x():\n    pass\n"))
    assert "solution raised ValueError: nope" in result.detail


def test_broken_tests_are_reported() -> None:
    result = check_exercise(make("x = 1\n", "def test_x(:\n"))
    assert "tests failed to load" in result.detail


def test_system_exit_in_solution_is_allowed() -> None:
    assert check_exercise(make("x = 1\nraise SystemExit(0)\n", "def test_x():\n    assert x == 1\n")).ok


def test_missing_solution() -> None:
    assert "no reference solution" in check_exercise(make("  \n", "")).detail


def test_timeout() -> None:
    result = check_exercise(make("while True:\n    pass\n", ""), timeout=1)
    assert result.detail == "timed out after 1s"


def test_harness_crash() -> None:
    result = check_exercise(make("import os\nos._exit(3)\n", ""))
    assert "harness crashed" in result.detail


def test_run_pytest_reports_real_results_and_grades_planted_bugs() -> None:
    learner = (
        "def test_rate(monkeypatch):\n"
        "    import billing\n"
        "    monkeypatch.setattr(billing, 'RATE', 0.5)\n"
        "    assert billing.total(100) == 150\n"
    )
    tests = (
        "good = 'RATE = 0.2\\ndef total(c):\\n    return round(c * (1 + RATE))\\n'\n"
        "bad = 'RATE = 0.2\\ndef total(c):\\n    return c\\n'\n"
        "def test_correct_version_passes():\n"
        "    code, report = run_pytest(learner_source, '-q', modules={'billing': good})\n"
        "    assert code == 0, report\n"
        "def test_planted_bug_is_caught():\n"
        "    code, report = run_pytest(learner_source, '-q', modules={'billing': bad})\n"
        "    assert code == 1, report\n"
        "    assert 'assert 100 == 150' in report\n"
    )
    result = check_exercise(make(learner, tests))
    assert result.ok, result.detail


def test_run_pytest_exposes_builtin_fixtures() -> None:
    learner = (
        "import logging\n"
        "def test_fixtures(tmp_path, capsys, caplog):\n"
        "    (tmp_path / 'a').write_text('x')\n"
        "    print('hello')\n"
        "    assert capsys.readouterr().out == 'hello\\n'\n"
        "    logging.getLogger('a').warning('careful')\n"
        "    assert 'careful' in caplog.text\n"
    )
    tests = "def test_ok():\n    code, report = run_pytest(learner_source, '-q')\n    assert code == 0, report\n"
    result = check_exercise(make(learner, tests))
    assert result.ok, result.detail
