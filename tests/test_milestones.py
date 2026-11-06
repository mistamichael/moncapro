"""
Meilensteine: Modell, Auflösung (auch für Loop-Tasks), Charts und API
=====================================================================
"""

from moncapro.paths import get_cfg_dir, get_examples_dir

import pytest

from moncapro.api import ProjectSession
from moncapro.milestones import resolve_milestones, unresolved_milestones
from moncapro.models import load_project, load_project_from_dict, save_project
from moncapro.schedule import build_schedule


def _schedule(name: str, milestones: list):
    data = load_project(get_examples_dir() / f"{name}.json").model_dump(by_alias=True, exclude_unset=True)
    data["milestones"] = milestones
    return build_schedule(load_project_from_dict(data), cfg_dir=get_cfg_dir())


def test_start_and_end_of_task():
    schedule = _schedule("hausbau", [{"id": "M1", "name": "Fundament fertig", "ref": 3},
                                     {"id": "M2", "name": "Ausbau", "ref": "8", "at": "start"}])
    m1, m2 = resolve_milestones(schedule)
    assert m1.days == schedule.cpm.tasks[3].fez
    assert m2.days == schedule.cpm.tasks[8].faz          # ref als Text trifft die Zahl-ID
    assert m1.when == schedule.cpm.date_at(m1.days, is_end=True)
    assert m1.describe("de")[0] == "M1 – Fundament fertig"
    assert "Ende von [3]" in m1.describe("de")[2]
    assert "Start of [8]" in m2.describe("en")[2]


def test_loop_task_spans_all_cycles():
    schedule = _schedule("erdaushub", [{"id": "A", "name": "Beginn", "ref": 2, "at": "start"},
                                       {"id": "E", "name": "Fertig", "ref": 2}])
    cycles = [schedule.cpm.tasks[t.id] for t in schedule.project.tasks if t.original_id == 2]
    assert len(cycles) > 1
    start, end = resolve_milestones(schedule)
    assert start.days == min(c.faz for c in cycles)
    assert end.days == max(c.fez for c in cycles)


def test_unknown_task_is_skipped_and_reported():
    schedule = _schedule("hausbau", [{"id": "MX", "name": "?", "ref": 99}])
    assert resolve_milestones(schedule) == []
    assert [m.id for m in unresolved_milestones(schedule.source)] == ["MX"]


def test_roundtrip(tmp_path):
    schedule = _schedule("hausbau", [{"id": "M1", "name": "Fundament fertig", "ref": 3, "note": "Abnahme"}])
    save_project(schedule.source, tmp_path / "p.json")
    loaded = load_project(tmp_path / "p.json")
    assert loaded.milestones[0].model_dump(exclude_unset=True) == {
        "id": "M1", "name": "Fundament fertig", "ref": 3, "note": "Abnahme"}


def test_invalid_anchor_rejected():
    with pytest.raises(ValueError):
        load_project_from_dict({"project": "x", "tasks": [], "milestones": [
            {"id": "M1", "name": "x", "ref": 1, "at": "middle"}]})


def test_charts_draw_one_line_per_milestone():
    pytest.importorskip("plotly")
    from moncapro.charts import build_gantt_figure, build_resource_figure

    schedule = _schedule("software_simple", [{"id": "M1", "name": "Design fertig", "ref": 3},
                                             {"id": "M2", "name": "Test beginnt", "ref": 6, "at": "start"}])
    for fig in (build_gantt_figure(schedule), build_resource_figure(schedule)):
        lines = [tr for tr in fig.data if tr.legendgroup == "milestones"]
        assert len(lines) == 2
        assert len(set(lines[0].x)) == 1 and "Design fertig" in lines[0].hovertext[0]
        assert [a.text for a in fig.layout.annotations if a.text in ("M1", "M2")] == ["M1", "M2"]


def test_api_lists_and_validates_milestones():
    s = ProjectSession()
    s.new_project("Garage", project_start="2026-04-01")
    s.add_task({"name": "Fundament", "duration": "3d"})
    s.upsert_item("milestones", {"id": "M1", "name": "Fundament fertig", "ref": 1})
    assert s.calculate()["milestones"] == [{"id": "M1", "name": "Fundament fertig", "ref": 1, "at": "end",
                                            "date": "2026-04-07", "days": 3.0}]   # Ostern
    s.upsert_item("milestones", {"id": "M2", "name": "?", "ref": 7})
    assert s.validate() == ["Meilenstein M2: unbekannter Task 7"]
