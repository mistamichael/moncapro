"""
Format-Version der Projektdatei (schema_version)
================================================

Alte Dateien ohne Feld laden weiter (gelten als Version 1), neuere Versionen werden mit klarer Meldung
abgelehnt statt Felder still zu verlieren, und Migrationen laufen Schritt für Schritt.
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from moncapro.api import ApiError, ProjectSession
from moncapro.models import (SCHEMA_VERSION, Project, SchemaVersionError, load_project, load_project_from_dict,
                             migrate_project_data, save_project)
from moncapro.models import schema as schema_module

LEGACY = {"project": "Alt", "tasks": [{"id": 1, "name": "A", "duration": "1d", "successors": []}]}


def _write(tmp_path: Path, data: dict, name: str = "p.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_current_version_is_a_positive_integer():
    assert isinstance(SCHEMA_VERSION, int) and SCHEMA_VERSION >= 1


def test_file_without_field_counts_as_version_1(tmp_path):
    project = load_project(_write(tmp_path, LEGACY))
    assert project.schema_version == 1 <= SCHEMA_VERSION


def test_saving_writes_the_version_as_first_field(tmp_path):
    out = tmp_path / "out.json"
    save_project(load_project(_write(tmp_path, LEGACY)), out)
    saved = json.loads(out.read_text(encoding="utf-8"))
    assert list(saved)[0] == "schema_version" and saved["schema_version"] == SCHEMA_VERSION
    assert load_project(out).project == "Alt"                       # lässt sich wieder laden


def test_new_project_without_file_gets_the_current_version(tmp_path):
    out = tmp_path / "neu.json"
    save_project(Project(project="Neu"), out)
    assert json.loads(out.read_text(encoding="utf-8"))["schema_version"] == SCHEMA_VERSION


@pytest.mark.parametrize("loader", ["file", "dict", "model"])
def test_newer_version_is_rejected_with_a_clear_message(tmp_path, loader):
    data = {**LEGACY, "schema_version": SCHEMA_VERSION + 1}
    with pytest.raises((SchemaVersionError, ValidationError)) as info:
        if loader == "file":
            load_project(_write(tmp_path, data))
        elif loader == "dict":
            load_project_from_dict(data)
        else:
            Project(**data)
    message = str(info.value)
    assert str(SCHEMA_VERSION + 1) in message and "pip install -U moncapro" in message


@pytest.mark.parametrize("value", [0, -1, "1", 1.5, True, None])
def test_invalid_version_values_are_rejected(value):
    with pytest.raises((SchemaVersionError, ValidationError)):
        load_project_from_dict({**LEGACY, "schema_version": value})


def test_migration_runs_step_by_step_and_keeps_the_input(monkeypatch):
    monkeypatch.setattr(schema_module, "SCHEMA_VERSION", 3)
    monkeypatch.setattr(schema_module, "_MIGRATIONS", {
        1: lambda d: {**{k: v for k, v in d.items() if k != "alt"}, "neu": d["alt"]},      # 1 → 2: Feld umbenannt
        2: lambda d: {**d, "extra": True},                                                 # 2 → 3: Feld ergänzt
    })
    data = {"project": "x", "alt": 7}
    migrated = migrate_project_data(data)
    assert migrated == {"project": "x", "neu": 7, "extra": True, "schema_version": 3}
    assert data == {"project": "x", "alt": 7}                                              # Eingabe unverändert
    assert migrate_project_data({"project": "x", "schema_version": 2, "neu": 1}) == {
        "project": "x", "neu": 1, "extra": True, "schema_version": 3}


def test_missing_migration_step_is_reported(monkeypatch):
    monkeypatch.setattr(schema_module, "SCHEMA_VERSION", 2)
    monkeypatch.setattr(schema_module, "_MIGRATIONS", {})
    with pytest.raises(SchemaVersionError, match="Keine Migration"):
        migrate_project_data({"project": "x"})


def test_api_reports_the_version_and_keeps_the_project_on_a_newer_one():
    session = ProjectSession()
    session.new_project("Neu")
    assert list(session.get_project())[0] == "schema_version"
    assert session.get_project()["schema_version"] == SCHEMA_VERSION
    revision = session.revision
    with pytest.raises(ApiError, match="Format-Version"):
        session.replace_project({**LEGACY, "schema_version": SCHEMA_VERSION + 1})
    assert session.revision == revision and session.get_project()["project"] == "Neu"


def test_api_accepts_a_legacy_dict_without_version():
    session = ProjectSession()
    session.replace_project(dict(LEGACY))
    assert session.get_project()["schema_version"] == SCHEMA_VERSION


def test_json_schema_documents_the_field():
    assert "schema_version" in ProjectSession.schema()["properties"]


def test_cli_reports_a_newer_version_in_one_line_and_fails(tmp_path, monkeypatch, capsys):
    from moncapro.cli import main

    monkeypatch.setenv("MONCAPRO_LOG", str(tmp_path / "log"))
    monkeypatch.setenv("MONCAPRO_RESULTS", str(tmp_path / "results"))
    path = _write(tmp_path, {**LEGACY, "schema_version": SCHEMA_VERSION + 1}, "neu.json")
    assert main(["--project", str(path), "--export", "json"]) == 1
    output = capsys.readouterr().out
    assert "Format-Version" in output and "Traceback" not in output
