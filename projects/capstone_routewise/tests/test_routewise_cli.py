"""Milestone 9: the command-line interface, end to end with temporary files."""

import pytest
from routewise.cli import main
from routewise.data import load_city
from routewise.store import Store


@pytest.fixture
def city_dir(tmp_path, capsys):
    out = tmp_path / "city"
    assert main(["generate", "--customers", "35", "--seed", "4", "--out", str(out)]) == 0
    capsys.readouterr()
    return out


def test_generate_writes_city(city_dir):
    city = load_city(city_dir)
    assert len(city.customers) == 35, "generate must honour --customers"


def test_plan_stores_feasible_plan(city_dir, tmp_path, capsys):
    db = tmp_path / "rw.db"
    assert main(["plan", "--city", str(city_dir), "--db", str(db), "--method", "sweep"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("plan 1:") and "feasible" in out
    with Store(db) as store:
        plan = store.load_plan(1)
    assert plan.method == "sweep" and sorted(plan.customers()) == list(range(1, 36))


def test_report_markdown_to_stdout(city_dir, tmp_path, capsys):
    db = tmp_path / "rw.db"
    main(["plan", "--city", str(city_dir), "--db", str(db)])
    capsys.readouterr()
    assert main(["report", "--city", str(city_dir), "--db", str(db)]) == 0
    out = capsys.readouterr().out
    assert "# RouteWise daily report (savings)" in out and "Customers served | 35" in out


def test_full_round_trip_with_simulation_and_file_output(city_dir, tmp_path, capsys):
    db, report = tmp_path / "rw.db", tmp_path / "report.txt"
    main(["plan", "--city", str(city_dir), "--db", str(db), "--capacity", "30", "--simulate", "--seed", "3"])
    main(["plan", "--city", str(city_dir), "--db", str(db), "--method", "nearest", "--no-improve"])
    capsys.readouterr()
    code = main(
        ["report", "--city", str(city_dir), "--db", str(db), "--plan", "1", "--format", "text", "--out", str(report)]
    )
    assert code == 0 and report.exists(), "--out must write the report file"
    text = report.read_text(encoding="utf-8")
    assert "Actual on-time" in text, "a simulated day must report actual on-time performance"
    assert "/ 30" in text, "the stored capacity must be used for the report"


def test_report_missing_plan_fails(city_dir, tmp_path, capsys):
    db = tmp_path / "rw.db"
    assert main(["report", "--city", str(city_dir), "--db", str(db)]) == 1, "an empty database is an error"
    main(["plan", "--city", str(city_dir), "--db", str(db)])
    assert main(["report", "--city", str(city_dir), "--db", str(db), "--plan", "99"]) == 1
    assert "no plan with id 99" in capsys.readouterr().err


def test_bad_arguments_exit_with_usage_error(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["plan"])
    assert exc.value.code == 2, "argparse reports usage errors with exit code 2"
    with pytest.raises(SystemExit):
        main(["fly"])
