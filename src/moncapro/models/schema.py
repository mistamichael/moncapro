"""
Format-Version der Projektdatei
===============================

Jede Projektdatei trägt ``schema_version`` (ganze Zahl). Damit lässt sich das Dateiformat später ändern, ohne
vorhandene Dateien zu brechen:

- Fehlt das Feld, ist es eine Datei aus der Zeit vor der Versionierung und gilt als Version 1.
- Ist die Version **älter** als ``SCHEMA_VERSION``, bringt ``migrate_project_data`` die Daten Schritt für
  Schritt auf den aktuellen Stand (je Schritt eine Funktion in ``_MIGRATIONS``).
- Ist die Version **neuer**, lehnt moncapro die Datei mit einer klaren Meldung ab – statt Felder still
  zu ignorieren und beim Speichern zu verlieren.

Wann erhöhen? Nur bei einer Änderung, die ältere moncapro-Versionen nicht mehr richtig lesen können
(Feld umbenannt oder entfernt, andere Bedeutung). Neue optionale Felder brauchen keine neue Version.
"""

from typing import Any, Callable, Dict

SCHEMA_VERSION = 1
"""Format-Version, die diese moncapro-Version schreibt und höchstens liest."""

# Schritte von Version n auf n + 1: {n: Funktion(dict) -> dict}. Aktuell gibt es nur Version 1.
_MIGRATIONS: Dict[int, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}


class SchemaVersionError(ValueError):
    """Die Format-Version der Datei ist ungültig oder neuer, als diese moncapro-Version kennt."""


def check_schema_version(version: Any) -> int:
    """Prüft einen ``schema_version``-Wert und gibt ihn als ``int`` zurück (``SchemaVersionError`` sonst)."""
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise SchemaVersionError(f"Ungültige schema_version: {version!r} (erwartet eine ganze Zahl ab 1)")
    if version > SCHEMA_VERSION:
        raise SchemaVersionError(
            f"Die Projektdatei hat Format-Version {version}, diese moncapro-Version kennt höchstens "
            f"{SCHEMA_VERSION}. Bitte moncapro aktualisieren (pip install -U moncapro)."
        )
    return version


def migrate_project_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Bringt Projektdaten (dict aus der JSON-Datei) auf ``SCHEMA_VERSION``.

    Das übergebene dict wird nicht verändert. Fehlt ``schema_version``, gilt die Datei als Version 1.
    Das Ergebnis enthält immer ``schema_version``.
    """
    version = check_schema_version(data.get("schema_version", 1))
    migrated = dict(data)
    while version < SCHEMA_VERSION:
        step = _MIGRATIONS.get(version)
        if step is None:                                  # Programmierfehler: Version erhöht, Schritt vergessen
            raise SchemaVersionError(f"Keine Migration von Format-Version {version} auf {version + 1}")
        migrated = step(migrated)
        version += 1
    migrated["schema_version"] = version
    return migrated
