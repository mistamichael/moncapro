"""
Laden → Speichern aller Beispiel-Projekte muss das JSON unverändert lassen.

Einzige Ergänzung: Beim Speichern kommt ``schema_version`` (Format-Version) als erstes Feld hinzu,
sofern die Datei sie noch nicht hat.
"""

import json
from pathlib import Path

from moncapro.paths import get_examples_dir

import pytest

from moncapro.models import SCHEMA_VERSION, load_project, save_project

EXAMPLES = sorted(get_examples_dir().glob("*.json"))


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda p: p.stem)
def test_json_round_trip(example: Path, tmp_path: Path) -> None:
    out = tmp_path / example.name
    save_project(load_project(example), out)
    saved = json.loads(out.read_text(encoding="utf-8"))
    original = json.loads(example.read_text(encoding="utf-8"))
    assert list(saved)[0] == "schema_version" and saved["schema_version"] == SCHEMA_VERSION
    without_version = lambda d: {k: v for k, v in d.items() if k != "schema_version"}
    assert without_version(saved) == without_version(original)
