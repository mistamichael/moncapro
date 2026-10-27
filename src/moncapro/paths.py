"""
Paths
=====

Auflösung der Verzeichnisse. Die mitgelieferten Konfigurationen (cfg/) und
Beispiele (examples/) liegen im Paket; alles andere (Ergebnisse, Arbeitsdateien,
Logs) liegt im Arbeitsverzeichnis des Nutzers und lässt sich über Umgebungs-
variablen umlenken:

    MONCAPRO_CFG      Konfigurationsverzeichnis (Standard: mitgeliefertes cfg/)
    MONCAPRO_RESULTS  Ausgabeverzeichnis für Exporte (Standard: ./results)
    MONCAPRO_WORK     Arbeitsdateien, Default für neue Projekte (Standard: .)
    MONCAPRO_LOG      Logdateien (Standard: ./log)
    MONCAPRO_DATA     Eingabe-Projektdateien der CLI (Standard: ./data)
"""

import os
from pathlib import Path
from typing import Optional

PACKAGE_DIR = Path(__file__).resolve().parent


def env_path(name: str) -> Optional[Path]:
    """Wert von MONCAPRO_<name>; None wenn nicht gesetzt."""
    value = os.environ.get(f"MONCAPRO_{name}")
    return Path(value) if value else None


def get_cfg_dir() -> Path:
    """Konfigurationsverzeichnis ($MONCAPRO_CFG oder das mitgelieferte cfg/)."""
    return env_path("CFG") or PACKAGE_DIR / "cfg"


def get_examples_dir() -> Path:
    """Mitgelieferte Beispielprojekte."""
    return PACKAGE_DIR / "examples"


def get_results_dir(create: bool = True) -> Path:
    """Ausgabeverzeichnis für Exporte ($MONCAPRO_RESULTS oder ./results)."""
    path = env_path("RESULTS") or Path("results")
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def get_work_dir() -> Path:
    """Default-Speicherort für neue Projekte ($MONCAPRO_WORK oder aktuelles Verzeichnis)."""
    return env_path("WORK") or Path.cwd()


def get_log_dir() -> Path:
    """Logverzeichnis ($MONCAPRO_LOG oder ./log)."""
    return env_path("LOG") or Path("log")


def get_data_dir() -> Path:
    """Verzeichnis mit Projektdateien für die CLI ($MONCAPRO_DATA oder ./data)."""
    return env_path("DATA") or Path("data")
