# CLAUDE.md – Projektanweisungen für Claude Code

## Projektübersicht

**moncapro** (PyPI) ist der Rechenkern für Projektplanung mit CPM (Critical Path Method), Ressourcenplanung,
Szenarien, Monte-Carlo-Simulation und einer MCP-Schnittstelle für KI-Clients. Projekte sind JSON-Dateien.
Es ist aus [sproject](https://github.com/mistamichael/sproject) hervorgegangen; sproject ist der Desktop-Editor
(Dear PyGui) und nutzt dieses Paket. **Hier gibt es keinen GUI-Code.**

## Projektstruktur

```text
moncapro/
├── src/moncapro/        # Paket (src-Layout)
│   ├── schedule.py      # build_schedule(): Expansion → CPM → Leveling → Gantt → Kosten (einziger Rechenweg)
│   ├── exporters.py     # EXPORTERS-Registry, export_schedule()
│   ├── durations.py     # Dauer-Parsing/Formatierung, hours_per_day aus defaults.cfg
│   ├── work_calendar.py # WorkCalendar: Arbeitstage, Wochenenden, Feiertage (holidays-Bibliothek)
│   ├── models/          # Pydantic-Modelle: Project, Tasks, Dependencies, Resources, CPM, Gantt, Leveling
│   ├── scenarios.py, simulation.py, baseline.py, charts.py, time_axis.py
│   ├── *_export.py, excel_reports.py   # Exporte
│   ├── api.py           # ProjectSession: Operationen für KI/Skripte (dict rein/raus, validiert)
│   ├── mcp/             # MCP-Server (build_server(session)), HTTP; stdio nur für Skripte/Tests
│   ├── cli.py           # CLI (`moncapro`, `python -m moncapro`)
│   ├── paths.py         # Verzeichnisse (MONCAPRO_*-Variablen), Paketdaten
│   ├── cfg/             # mitgelieferte Konfiguration (defaults.cfg, *_export.cfg) – Package-Data
│   └── examples/        # mitgelieferte Beispielprojekte – Package-Data
├── tests/               # pytest; tests/golden/ = Referenz-Exporte aller Beispiele
├── doc/{de,en}/         # Dokumentation, doc/img/ Diagramme, doc/result_examples/ fertige Ergebnisse
└── .github/workflows/   # tests.yml (Matrix 3.12/3.13, Linux/Windows), publish.yml (Tag v* → TestPyPI → PyPI)
```

- Python ≥ 3.12, Datenmodelle **Pydantic**. Kern-Abhängigkeiten nur `pydantic` und `holidays`;
  alles andere sind Extras (`excel`, `html`, `svg`, `charts`, `mcp`, `all`, `dev`) und wird lazy importiert.
- Version steht nur in `src/moncapro/__init__.py` (`__version__`), `pyproject.toml` liest sie von dort.

## Architektur

1. **JSON** → `moncapro.models.load_project()` → **Pydantic `Project`**.
2. **Berechnung:** `build_schedule(project)` → `Schedule` (expandiertes Projekt, CPM, Gantt, Kosten).
   - Zeitumrechnung CPM-Arbeitstage → Kalender **nur** über `CPMResult.date_at(workdays, is_end)`.
   - CPM rechnet in Arbeitstagen; danach plant `models/leveling.py` mit Ressourcen (eine Person/ein LKW = eine
     Aufgabe zugleich, `Resource.slots`), Urlaub und Teilzeit sowie `not_before`/`deadline`. Mehrere
     Prioritätsregeln, der kürzeste Plan gewinnt. Ruhepausen kommen danach (zweiter CPM-Lauf).
   - Plan gegen Ist: `status_date`, `actuals`, `baseline` (`models/tracking.py`, `baseline.py`); Doku `doc/de/termine-und-ist.md`.
   - Szenarien: `scenarios` im Projekt (`models/scenario.py`), angewendet und verglichen in `scenarios.py`.
   - Monte-Carlo: `duration_range`/`risk` am Task, `probability` am Szenario → `simulation.py` (nutzt die im
     Basisplan gewählte Leveling-Regel). Liegt die geplante Dauer außerhalb von `duration_range`, nimmt die
     Simulation den Rand und meldet den Task (`planned_outside_range()`, `SimulationResult.clamped`).
3. **Export:** `export_schedule()` – JSON, Markdown, HTML, Excel, TXT, SVG-ZIP, Plotly.
4. **KI-Schnittstelle:** `api.py` (`ProjectSession`) → `mcp/server.py`; Doku `doc/de/ki-schnittstelle.md`.
   - **Genau ein Server** (HTTP, `moncapro-mcp --http`, Standard-Port 8765) hält das Projekt. Claude Code und
     weitere Clients (z. B. die sproject-GUI) sind nur Clients. Ein zweiter Start auf demselben Port bricht ab.
   - Änderungen laufen über das Projekt-dict und werden neu validiert (`_commit`, zählt `revision` hoch) –
     ungültige Eingaben ändern nichts.
   - **Projektwechsel** (`new_project`, `load`, `replace_project` ohne `base_revision` → `ProjectSession._switch`):
     vorher `write_backup()` nach `$MONCAPRO_WORK/backup`, `generation` + `last_switch` setzen, Antwort mit
     `warning`. Der Server merkt sich je MCP-Sitzung den gesehenen `generation`-Stand und lehnt den nächsten
     Aufruf eines Clients ab, wenn ein *anderer* Client gewechselt hat.
   - Tests mit Projektwechsel müssen `backup_dir` auf ein Temp-Verzeichnis setzen.
   - Im stdio-Modus nichts auf stdout schreiben – `print()` der Bibliothek wird im Server nach stderr umgeleitet.
5. **Speichern:** `save_project()` schreibt nur explizit gesetzte Felder (`exclude_unset`) → Laden/Speichern ist verlustfrei.

### Pfade und Umgebungsvariablen

`paths.py` kennt `MONCAPRO_CFG` (Standard: mitgeliefertes `cfg/`), `MONCAPRO_RESULTS` (`./results`),
`MONCAPRO_WORK` (aktuelles Verzeichnis), `MONCAPRO_LOG` (`./log`), `MONCAPRO_DATA` (`./data`).
Ein eigenes `MONCAPRO_CFG`-Verzeichnis **ersetzt** das mitgelieferte vollständig. Keine `PV_*`-Variablen
(die gehören zu sproject).

### Fallstricke

- **`save_project()` nutzt `exclude_unset`:** Listen in Modellen nicht in place ändern (`append`, `remove`),
  sondern neu zuweisen (`x.changes = x.changes + [c]`) – sonst gilt das Feld als ungesetzt und wird nicht gespeichert.
- **Package-Data:** Neue Dateien in `cfg/` oder `examples/` müssen im Wheel landen – nach Änderungen
  `python -m build` und Inhalt prüfen. Der Test gegen das installierte Wheel ist der verlässlichste.
- **Golden-Tests:** `tests/golden/` nur nach bewusster Ergebnisänderung neu erzeugen
  (`UPDATE_GOLDEN=1 python -m pytest tests/test_golden.py`).
- **Windows-Konsole:** Ausgaben mit Umlauten brauchen `PYTHONIOENCODING=utf-8`, wenn sie umgeleitet werden.

## Arbeitshinweise für Claude Code

- Veröffentlichen (Tag `v*` pushen, PyPI) nur auf ausdrückliche Anweisung des Nutzers.
- Nach Änderungen: `python -m pytest`; vor Releases zusätzlich `python -m build && python -m twine check dist/*`.
- Als toten Code markierte Symbole (vulture/skylos) nur entfernen, wenn der Nutzer dies bestätigt.
- Typ-Fehler (pyright/mypy) bei neu generiertem Code direkt beheben.
