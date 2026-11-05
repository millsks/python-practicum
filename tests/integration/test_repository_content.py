"""Whole-repository quality gates: the site is valid, every exercise and project is solvable."""

import re
from pathlib import Path

import pytest

from practicum.exercises import HARNESS, Exercise, check_exercise, check_page_exercises
from practicum.projects import Source, discover_projects, grade_project
from practicum.site import check_site
from tests.conftest import REPO_ROOT

pytestmark = pytest.mark.integration

PAGES = sorted((REPO_ROOT / "docs").rglob("*.html"))
PROJECTS = discover_projects(REPO_ROOT)


def test_site_has_no_issues() -> None:
    issues = check_site(REPO_ROOT / "docs")
    assert not issues, "\n".join(f"{i.path}: {i.message}" for i in issues)


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.relative_to(REPO_ROOT / "docs").as_posix())
def test_exercise_solutions_pass(page: Path) -> None:
    failures = [r for r in check_page_exercises(page) if not r.ok]
    assert not failures, "\n".join(f"{r.id}: {r.detail}" for r in failures)


@pytest.mark.parametrize("project", PROJECTS, ids=lambda p: p.id)
def test_project_solution_passes(project: object) -> None:
    assert grade_project(REPO_ROOT, project, source=Source.SOLUTION, extra_args=["-q", "-p", "no:randomly"]) == 0  # type: ignore[arg-type]


@pytest.mark.parametrize("project", PROJECTS, ids=lambda p: p.id)
def test_project_starter_is_unsolved(project: object) -> None:
    assert grade_project(REPO_ROOT, project, source=Source.STARTER, extra_args=["-q", "-x"]) != 0  # type: ignore[arg-type]


def test_library_styles_load_before_course_styles() -> None:
    # Regression: CodeMirror's stylesheet was appended after course.css and won every tie,
    # leaving editors white in dark mode and fixed at 300px tall.
    course_js = (REPO_ROOT / "docs" / "assets" / "js" / "course.js").read_text(encoding="utf-8")
    load_css = course_js[course_js.index("function loadCss") : course_js.index("const icon")]
    assert "first.before(link)" in load_css
    assert "head.append(h(" not in load_css


def test_lesson_pytest_cells_pass() -> None:
    # The component gallery's cell fails on purpose to show a real failure report, so it is not checked here.
    cell = re.compile(r'<div class="runnable" data-pytest[^>]*>\s*<textarea>(.*?)</textarea>', re.S)
    tests = "def test_cell():\n    code, report = run_pytest(learner_source, '-q')\n    assert code == 0, report\n"
    pages = [*(REPO_ROOT / "docs" / "modules").glob("*.html"), *(REPO_ROOT / "docs" / "projects").glob("*.html")]
    checked = 0
    for page in pages:
        for source in cell.findall(page.read_text(encoding="utf-8")):
            checked += 1
            result = check_exercise(Exercise(f"{page.name}#{checked}", source, tests, ""))
            assert result.ok, f"{page.name}: {result.detail}"
    assert checked >= 8


def test_run_pytest_matches_the_browser_runtime() -> None:
    pattern = re.compile(r"^def run_pytest\(.*?^    return int\(code\), buf\.getvalue\(\)$", re.S | re.M)
    course_js = (REPO_ROOT / "docs" / "assets" / "js" / "course.js").read_text(encoding="utf-8")
    browser, local = pattern.search(course_js), pattern.search(HARNESS)
    assert browser is not None
    assert local is not None
    assert browser.group() == local.group()
