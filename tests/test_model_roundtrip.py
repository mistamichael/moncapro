"""
Laden → Speichern aller Beispiel-Projekte muss das JSON unverändert lassen.
"""

import json
from pathlib import Path

from moncapro.paths import get_examples_dir

import pytest

from moncapro.models import load_project, save_project

EXAMPLES = sorted(get_examples_dir().glob("*.json"))


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda p: p.stem)
def test_json_round_trip(example: Path, tmp_path: Path) -> None:
    out = tmp_path / example.name
    save_project(load_project(example), out)
    assert json.loads(out.read_text(encoding="utf-8")) == json.loads(example.read_text(encoding="utf-8"))
