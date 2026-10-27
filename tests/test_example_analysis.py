"""
Szenarien und Monte-Carlo-Simulation am Beispielprojekt software_simple.json
(die Zahlen stehen in doc/de/examples.md und doc/en/examples.md).
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from moncapro.models import load_project
from moncapro.paths import get_examples_dir
from moncapro.scenarios import BASE_NAME, compare_scenarios, comparison_rows
from moncapro.simulation import simulate, summary_rows, top_critical

EXAMPLE = get_examples_dir() / "software_simple.json"
GOLDEN_DIR = Path(__file__).parent / "golden"
UPDATE = os.environ.get("UPDATE_GOLDEN") == "1"


def _table(rows) -> str:
    return "".join(" | ".join(str(c) for c in row) + "\n" for row in rows)


def _check_golden(name: str, actual: str) -> None:
    golden = GOLDEN_DIR / name
    if UPDATE or not golden.exists():
        golden.write_text(actual, encoding="utf-8", newline="\n")
        return
    assert actual == golden.read_text(encoding="utf-8"), f"{name} weicht von der Referenz ab"


@pytest.fixture(scope="module")
def project():
    return load_project(EXAMPLE)


def test_example_declares_uncertainties_and_scenarios(project):
    tasks = {t.id: t for t in project.tasks}
    assert tasks[4].duration_range == ["32h", "72h"]
    assert tasks[4].risk.probability == 0.2 and tasks[4].risk.delay == "16h"
    assert tasks[5].duration_range and tasks[6].duration_range
    probabilities = {s.name: s.probability for s in project.scenarios}
    assert len(probabilities) == 3
    assert sorted(p for p in probabilities.values() if p) == [0.15]    # nur ein Szenario geht in die Simulation ein


def test_scenarios_are_compared_with_the_base_plan(project):
    outcomes = {o.name: o for o in compare_scenarios(project)}
    assert list(outcomes)[0] == BASE_NAME
    sick, backend, deadline = (s.name for s in project.scenarios)
    assert outcomes[BASE_NAME].delta_days == 0
    assert round(outcomes[sick].delta_days * 8) == 40            # Ausfall: +40 h
    assert round(outcomes[backend].delta_days * 8) == 20         # Mehraufwand: +20 h
    assert outcomes[deadline].delta_days == 0                    # Deadline ändert den Plan nicht ...
    assert outcomes[deadline].deadline_violations == 1           # ... wird aber verfehlt
    assert outcomes[BASE_NAME].deadline_violations == 0


def test_simulation_is_reproducible_and_ordered(project):
    first, second = simulate(project, runs=300, seed=1), simulate(project, runs=300, seed=1)
    assert first.ends == second.ends
    assert first.percentile(50) <= first.percentile(80) <= first.percentile(90)
    assert first.ends[0] < first.result.project_end_days < first.ends[-1]
    assert first.probability_by(first.result.project_end_days) < 0.1       # Plan wird kaum gehalten
    assert 0.05 < first.scenario_hits[project.scenarios[0].name] < 0.3     # Szenario mit p = 0,15


def test_simulation_criticality_of_the_example(project):
    sim = simulate(project, runs=300, seed=1)
    critical = {row[0]: row[2] for row in top_critical(sim)}
    assert critical["6"] == critical["7"] == critical["8"] == "100%"       # Tail der Kette immer kritisch
    assert {"4", "5"} <= critical.keys()                                   # Entwicklung bestimmt oft das Ende


def test_cli_scenarios_and_simulate(tmp_path):
    def run(*args):
        return subprocess.run(
            [sys.executable, "-m", "moncapro", "--project", str(EXAMPLE), "--output-dir", str(tmp_path), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)

    scenarios = run("--scenarios")
    assert scenarios.returncode == 0, scenarios.stderr
    assert "Alice eine Woche krank" in scenarios.stdout + scenarios.stderr

    simulation = run("--simulate", "50", "--seed", "1", "--export", "simulation")
    assert simulation.returncode == 0, simulation.stderr
    assert list(tmp_path.glob("*simulation*.html"))


def test_scenario_comparison_matches_golden(project):
    _check_golden("software_simple_scenarios.txt", _table(comparison_rows(compare_scenarios(project))))


def test_simulation_summary_matches_golden(project):
    sim = simulate(project, runs=300, seed=1)
    _check_golden("software_simple_simulation.txt", _table(summary_rows(sim)) + _table(top_critical(sim)))
