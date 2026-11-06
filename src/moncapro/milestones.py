"""
Meilensteine
============

Löst die Meilensteine eines Projekts (models/milestone.py) gegen einen
berechneten Schedule auf: Anfang = FAZ, Ende = FEZ des Tasks. Bei
expandierten Loop-/Instanz-Tasks zählt der früheste Anfang bzw. das späteste
Ende aller Zyklen (original_id).

Meilensteine auf unbekannte Tasks werden übersprungen (unresolved_milestones()).
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from .models.milestone import Milestone
from .models.project import Project
from .schedule import Schedule

_LABELS = {
    'de': {'start': 'Anfang', 'end': 'Ende', 'of': 'von', 'date': 'Datum', 'workday': 'Arbeitstag'},
    'en': {'start': 'Start', 'end': 'End', 'of': 'of', 'date': 'Date', 'workday': 'Working day'},
}


@dataclass(frozen=True)
class MilestonePoint:
    """Aufgelöster Meilenstein: Zeitpunkt in Arbeitstagen seit Projektstart."""
    milestone: Milestone
    days: float
    task_name: str
    when: Optional[datetime]       # Kalenderzeitpunkt (None ohne Projektstart)

    @property
    def id(self) -> str:
        return self.milestone.id

    @property
    def label(self) -> str:
        """Kurzbeschriftung für die Linie im Chart."""
        return self.milestone.id

    def describe(self, lang: str = 'de') -> List[str]:
        """Zeilen für Tooltips: Name, Datum, Bezug, Notiz."""
        lb = _LABELS.get(lang, _LABELS['de'])
        m = self.milestone
        when = (f"{lb['date']}: {self.when:%Y-%m-%d %H:%M}" if self.when is not None
                else f"{lb['workday']}: {self.days:g}")
        lines = [f"{m.id} – {m.name}", when, f"{lb[m.at]} {lb['of']} [{m.ref}] {self.task_name}"]
        if m.note:
            lines.append(m.note)
        return lines


def _tasks_by_ref(schedule: Schedule) -> Dict[str, List]:
    """Task-ID (als Text) → CPM-Ergebnisse; expandierte Tasks auch unter ihrer original_id."""
    by_ref: Dict[str, List] = {}
    for task in schedule.project.tasks:
        result = schedule.cpm.tasks.get(task.id)
        if result is None:
            continue
        keys = {str(task.id)}
        original_id = getattr(task, 'original_id', None)
        if original_id is not None:
            keys.add(str(original_id))
        for key in keys:
            by_ref.setdefault(key, []).append(result)
    return by_ref


def resolve_milestones(schedule: Schedule) -> List[MilestonePoint]:
    """Alle auflösbaren Meilensteine, nach Zeitpunkt sortiert."""
    milestones = (schedule.source or schedule.project).milestones or []
    if not milestones:
        return []
    by_ref = _tasks_by_ref(schedule)
    names = {str(t.id): t.name for t in (schedule.source or schedule.project).tasks}
    cpm = schedule.cpm
    points = []
    for m in milestones:
        results = by_ref.get(str(m.ref))
        if not results:
            continue
        days = min(r.faz for r in results) if m.at == 'start' else max(r.fez for r in results)
        when = cpm.date_at(days, is_end=m.at == 'end') if cpm.project_start is not None else None
        points.append(MilestonePoint(m, days, names.get(str(m.ref), results[0].name), when))
    return sorted(points, key=lambda p: p.days)


def unresolved_milestones(project: Project) -> List[Milestone]:
    """Meilensteine, deren ref auf keinen Task des Projekts zeigt."""
    ids = {str(t.id) for t in project.tasks}
    return [m for m in (project.milestones or []) if str(m.ref) not in ids]
