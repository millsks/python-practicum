"""Whole-repository quality gates: the site is valid, every exercise and project is solvable."""

from pathlib import Path

import pytest

from practicum.exercises import check_page_exercises
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
