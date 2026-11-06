"""
Project loader
==============

Lädt Projekt-JSON-Dateien als einheitliches Project-Modell.
"""

import json
from pathlib import Path
from typing import Union
from pydantic import ValidationError

from .project import Project
from .schema import SCHEMA_VERSION, migrate_project_data


def load_project(file_path: Union[str, Path]) -> Project:
    """
    Lädt eine Projekt-JSON-Datei.

    Args:
        file_path: Pfad zur JSON-Datei

    Returns:
        Project-Modell

    Raises:
        ValidationError: Wenn die JSON-Struktur ungültig ist
        SchemaVersionError: Wenn die Datei eine neuere Format-Version hat, als diese moncapro-Version kennt
        FileNotFoundError: Wenn die Datei nicht existiert
        json.JSONDecodeError: Wenn die Datei kein gültiges JSON enthält

    Ältere Format-Versionen (und Dateien ohne ``schema_version``) werden beim Laden auf den aktuellen Stand gebracht.
    """
    file_path = Path(file_path)

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    try:
        return Project(**migrate_project_data(data))
    except ValidationError:
        print(f"Validation error in {file_path}:")
        raise


def load_project_from_dict(data: dict) -> Project:
    """
    Lädt ein Projekt aus einem Dictionary.

    Args:
        data: Dictionary mit Projektdaten

    Returns:
        Project-Modell

    Ältere Format-Versionen werden wie in ``load_project`` auf den aktuellen Stand gebracht.
    """
    return Project(**migrate_project_data(data))



def save_project(project: Project, file_path: Union[str, Path], indent: int = 2) -> None:
    """
    Speichert ein Projekt-Modell als JSON-Datei.

    Args:
        project: Pydantic-Projekt-Modell
        file_path: Ziel-Pfad für JSON-Datei
        indent: JSON-Einrückung (Standard: 2)

    Examples:
        >>> project = load_project("examples/software_simple.json")
        >>> save_project(project, "output/project_copy.json")
    """
    file_path = Path(file_path)

    # Stelle sicher, dass Verzeichnis existiert
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Exportiere mit Aliasen (z.B. "from" statt "from_")
    data = project.model_dump(by_alias=True, exclude_none=True, exclude_unset=True)
    data.pop('schema_version', None)
    data = {'schema_version': SCHEMA_VERSION, **data}     # Format-Version immer, als erstes Feld

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
