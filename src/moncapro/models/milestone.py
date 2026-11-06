"""
Milestone model
===============

Benannter Zeitpunkt am Anfang oder Ende eines Tasks:

    "milestones": [
        {"id": "M1", "name": "Rohbau fertig", "ref": 5, "at": "end"}
    ]

ref ist die Task-ID wie im Projekt (bei Loop-/Instanz-Tasks die ID des
ursprünglichen Tasks: Anfang = erster Zyklus, Ende = letzter Zyklus).
Aufgelöst wird in moncapro/milestones.py.
"""

from typing import Literal, Optional, Tuple, Union

from pydantic import BaseModel

Anchor = Literal['start', 'end']
MILESTONE_ANCHORS: Tuple[Anchor, ...] = ('start', 'end')


class Milestone(BaseModel):
    id: str
    name: str
    ref: Union[int, str]                        # Task-ID
    at: Anchor = 'end'                          # Anfang oder Ende des Tasks
    note: Optional[str] = None
