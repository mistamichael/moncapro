# KI-Schnittstelle (MCP)

Mit der KI-Schnittstelle kann ein KI-Werkzeug wie Claude Code oder Claude Desktop Projekte
anlegen, aus Excel-Listen oder anderen Quellen aufbauen, prüfen, berechnen und speichern.
Python-Skripte nutzen dieselben Operationen direkt.

> English version: [doc/en/ai-interface.md](../en/ai-interface.md)

## Grundidee: genau ein moncapro-Server

```text
Claude Code / Claude Desktop          weitere Clients (z. B. eine GUI)
        │  MCP über HTTP                      │  MCP über HTTP
        └──────────────┬──────────────────────┘
                       ▼
        moncapro-Server  (moncapro-mcp --http, http://127.0.0.1:8765/mcp)
        moncapro.mcp.server → moncapro.api.ProjectSession → hält DAS Projekt
                       ▼
        moncapro.models, build_schedule, Exporter, Szenarien, Simulation
```

- **Ein** Server läuft und hält **ein** Projekt. Alle Clients sehen denselben Stand – es gibt keine zweite,
  versteckte Kopie.
- Ein zweiter Server auf demselben Port startet nicht ("Port 8765 ist belegt – läuft schon ein moncapro-Server?").
- Die KI liest Quelldaten (Excel, PDF, Text) selbst und überträgt sie mit den Werkzeugen ins Projekt.
- Jede Änderung wird sofort validiert. Ungültige Eingaben ändern nichts und liefern eine Fehlermeldung.
- Die Berechnung läuft über `build_schedule()` – dieselben Ergebnisse wie in der CLI.

## Einrichtung

### 1. Installieren und Server starten

```bash
pip install "moncapro[mcp]"
moncapro-mcp --http                     # HTTP auf http://127.0.0.1:8765/mcp
moncapro-mcp --http --port 8766         # anderer Port
moncapro-mcp --http --project DATEI     # Projekt beim Start öffnen
moncapro-mcp --help
```

Das Terminal zeigt die Adresse; Beenden mit Strg+C. Der Server lauscht nur auf `127.0.0.1` und ist damit
nur vom eigenen Rechner erreichbar. `python -m moncapro.mcp --http` ist gleichwertig.

### 2. Claude Code verbinden

```bash
claude mcp add --transport http moncapro http://127.0.0.1:8765/mcp
```

oder eine `.mcp.json` in den Arbeitsordner legen:

```json
{"mcpServers": {"moncapro": {"type": "http", "url": "http://127.0.0.1:8765/mcp"}}}
```

Claude Code in diesem Ordner starten und den Server `moncapro` einmal bestätigen; `/mcp` zeigt den Status.
Läuft der Server noch nicht, meldet Claude Code die Verbindung als fehlgeschlagen – Server starten, dann in
`/mcp` neu verbinden. Bei anderem Port die URL anpassen.

### 3. Weitere Clients (optional)

Jeder MCP-Client kann das Projekt mit Claude teilen. Für Clients, die das Projekt interaktiv bearbeiten,
gibt es `get_revision` (günstiger Änderungszähler) und `get_state` (Zähler + Projekt + Pfad) sowie
`replace_project(data, base_revision)` zum Zurückschreiben. Konfliktregel: Hat sich der Stand auf dem Server
inzwischen geändert, wird das Schreiben abgelehnt – **die Serverversion gilt**. Die sproject-GUI ist so ein Client.

### stdio-Modus (Sonderfall)

`moncapro-mcp` ohne `--http` startet einen Server über stdio, z. B. für einen MCP-Client, der den Server
selbst startet, oder für Tests. Ein solcher Server gehört **nur diesem einen Client**. Für gemeinsames
Arbeiten immer den HTTP-Server verwenden. Im stdio-Modus nie auf stdout schreiben – `print()`-Ausgaben der
Bibliothek werden nach stderr umgeleitet.

## Schnellstart: neues Projekt aus einer Excel-Datei

1. Server starten: `moncapro-mcp --http`
2. Claude Code starten und mit `/mcp` prüfen, dass `moncapro` verbunden ist.
3. Claude zum Beispiel bitten:

   > Lies `webshop.xlsx` und baue daraus ein neues moncapro-Projekt: Stammdaten aus dem Blatt "Projekt",
   > Personen und Ressourcen aus "Team", Aufgaben mit Abhängigkeiten aus "Aufgaben". Weise jede Aufgabe der
   > verantwortlichen Person zu, nutze min/max als Unsicherheit und setze für den Go-live die Deadline
   > 15.12.2026. Prüfe das Projekt, berechne es, nenne Endtermin, Kosten und kritischen Pfad, simuliere 300
   > Läufe und speichere es als `webshop.json`.

Claude liest die Excel-Datei selbst und ruft dann nacheinander die Werkzeuge auf: `new_project`, `upsert_item`
(Personen und Ressourcen), `add_task` (die Antwort enthält die Task-ID), `add_dependency` (Vorgänger →
Nachfolger mit diesen IDs), `set_uncertainty`, `update_task` (Deadline), `validate`, `calculate`, `simulate`
und `save_project` (relative Pfade landen im Arbeitsordner, `$MONCAPRO_WORK`).

Eigene Excel-Dateien brauchen kein festes Format: Blätter und Spalten in der Anfrage beschreiben; Claude
fragt nach, wenn etwas unklar ist.

## Projektwechsel und Sicherungen

Der Server hält genau ein Projekt. Wird es **als Ganzes ersetzt**, sichert der Server zuerst den bisherigen
Stand nach `<Arbeitsordner>/backup/<Zeitstempel>_<Projektname>.json` (Arbeitsordner: `$MONCAPRO_WORK`,
Standard das aktuelle Verzeichnis) und meldet den Wechsel:

| Auslöser | Meldung |
| --- | --- |
| `new_project`, `load_project`, `replace_project` ohne `base_revision` | die Antwort enthält `warning` mit altem/neuem Projekt und Sicherungspfad |
| ein anderer Client hat das Projekt ersetzt | der **nächste** Aufruf der übrigen Clients wird **nicht ausgeführt** und meldet den Wechsel samt Sicherungspfad; ein erneuter Aufruf funktioniert dann |

Außerdem:

- Das Server-Terminal protokolliert jeden Wechsel (`[moncapro] Projekt ersetzt: …`).
- Das Projekt wird nur ersetzt, wenn die neuen Daten gültig sind – sonst bleibt alles unverändert (keine Sicherung).
- Eine Sicherung wird wie jede Projektdatei geladen, z. B. von Claude mit `load_project`
  ("Lade die neueste Sicherung aus dem Backup-Ordner").
- Zum Ändern des bestehenden Projekts nutzt Claude `patch_project`, `add_task` usw. – das ist kein Wechsel.

## Beispiele für Anfragen an Claude

- "Lies `bauplan.xlsx` (Spalten: Nr., Tätigkeit, Dauer in Tagen, Vorgänger) und baue ein moncapro-Projekt mit
  Start am 4.5.2026. Prüfe es, berechne es und speichere es als `bauplan.json`."
- "Ergänze im offenen Projekt die Personen Anna (Maurerin, 55 €/h) und Ben (Zimmermann, 60 €/h), weise sie den
  passenden Aufgaben zu und sag mir, wie sich Endtermin und Kosten ändern."
- "Lege ein Szenario 'Fensterlieferung verspätet' an, in dem Aufgabe 7 zehn Tage später starten kann, und
  vergleiche es mit dem Basisplan."
- "Schätze für alle Aufgaben eine min/max-Dauer und simuliere: Bis wann sind wir zu 80 % fertig?"

## Typischer Ablauf der KI

```text
new_project / load_project
  → add_task (je Aufgabe; die Antwort enthält die vergebene ID)
  → add_dependency (mit den IDs aus add_task)
  → upsert_item (Personen, Ressourcen) → update_task (Ressourcen zuweisen)
  → validate → calculate → save_project
```

Bei großen Listen geht es mit einem Aufruf schneller: `patch_project({"tasks": [...]})` oder
`replace_project({...})` mit dem vollständigen Projekt im JSON-Format (Schema: `moncapro://schema`).

## Werkzeuge (MCP)

| Werkzeug | Zweck / Ergebnis |
| --- | --- |
| `new_project`, `load_project` | Projekt anlegen / öffnen → Kurzfassung |
| `save_project` | speichern (relative Pfade → Arbeitsordner) → Dateipfad |
| `get_overview`, `get_project` | Kurzfassung bzw. vollständiges JSON |
| `replace_project` | ganzes Projekt ersetzen (Projektwechsel mit Sicherung und `warning`); mit `base_revision` nur Änderung eines bekannten Stands |
| `patch_project` | Felder der obersten Ebene setzen (Massenaufbau im bestehenden Projekt, kein Wechsel) |
| `add_task` | Task anlegen → gespeicherter Task **inkl. `id`** (ohne `id` wird die nächste Nummer vergeben) |
| `get_task`, `update_task`, `remove_task` | Task lesen, ändern (`null` entfernt ein Feld), löschen |
| `add_dependency`, `remove_dependency` | Abhängigkeiten EA (Standard, Ende-Anfang), AA, EE, AE |
| `set_uncertainty` | `duration_range` und `risk` für die Simulation |
| `upsert_item`, `remove_item`, `set_list` | Ressourcen, Personen, Ruhezeiten, Szenarien |
| `validate` | unbekannte Referenzen, Zyklen, Rechenfehler → Liste (leer = in Ordnung) |
| `calculate` | Start, Ende, kritischer Pfad, Kosten, Terminwarnungen, Termine je Task |
| `compare_scenarios`, `simulate` | Szenario-Vergleich, Monte-Carlo |
| `export` | Berichte (json, txt, md, html, xlsx, …) nach `$MONCAPRO_RESULTS` (Standard `./results`) |
| `list_examples` | Beispielprojekte als Vorlagen |
| `get_revision`, `get_state` | Änderungszähler bzw. Zähler + Projekt + Pfad (für interaktive Clients) |

MCP-Ressourcen: `moncapro://schema` (JSON-Schema des Projektformats), `moncapro://examples/<name>`.

## Ohne MCP aus Python

Für Skripte ohne Server – arbeitet auf einem eigenen Projekt im Speicher:

```python
from moncapro.api import ProjectSession, ApiError

s = ProjectSession()
s.new_project("Garage", project_start="2026-04-01")
fundament = s.add_task({"name": "Fundament", "duration": "3d"})   # → Task-ID (hier 1)
waende = s.add_task({"name": "Wände", "duration": "5d"})
dach = s.add_task({"name": "Dach", "duration": "2d"})
s.add_dependency(fundament, waende)
s.add_dependency(waende, dach)

s.upsert_item("persons", {"id": "P1", "name": "Anna", "role": "Maurerin", "hourly_rate": 55})
s.upsert_item("resources", {"id": "R1", "type": "person", "person_id": "P1"})
s.update_task(waende, {"resources": ["R1"]})

assert s.validate() == []
result = s.calculate()
print(result["end"], result["total_costs"], [t["name"] for t in result["critical_path"]])
s.save("garage.json")
s.export(["xlsx", "html"])

try:
    s.add_dependency(dach, 99)
except ApiError as e:
    print(e)          # Task 99 nicht gefunden – das Projekt bleibt unverändert
```

| Methode | Rückgabe |
| --- | --- |
| `new_project(name, project_start, unit)` | Kurzfassung (dict) |
| `load(path)`, `replace_project(data, base_revision=None)`, `patch_project(fields)` | Kurzfassung (dict) |
| `save(path=None)` | Pfad als Text |
| `get_project()`, `overview()`, `list_tasks()`, `schema()` | Projekt-JSON, Kurzfassung, Task-Liste, JSON-Schema |
| `add_task(task)` | **Task-ID** |
| `get_task(id)`, `update_task(id, fields)`, `set_uncertainty(id, …)` | Task (dict, normalisiert, z. B. `"5"` → `"5d"`) |
| `remove_task(id)` | verbleibende Task-IDs |
| `add_dependency(vorgänger, nachfolger, dep_type="EA")`, `remove_dependency(…)` | Vorgänger-Task (dict) |
| `upsert_item(field, item)`, `remove_item(field, key)`, `set_list(field, items)` | Eintrag bzw. Anzahl |
| `validate()` | Liste von Problemen (leer = in Ordnung) |
| `calculate(start_date=None)` | dict: `start`, `end`, `duration_days`, `critical_path`, `total_costs`, `deadline_warnings`, `tracking`, `tasks` |
| `export(formats, out_dir=None)` | Liste der erzeugten Dateien |
| `compare_scenarios()`, `simulate(runs, seed)` | Tabelle bzw. dict mit `summary` und `top_critical` |
| `revision`, `state()` | Änderungszähler bzw. `{"revision", "project", "path"}` |

Fehler werden als `ApiError` (Unterklasse von `ValueError`) mit verständlicher Meldung ausgelöst.

## Fehlerbehebung

| Problem | Lösung |
| --- | --- |
| "Port 8765 ist belegt – läuft schon ein moncapro-Server?" | Es läuft bereits ein Server – diesen verwenden. Sonst anderer Port: `--port 8766` (dann auch die URL im Client anpassen) |
| Claude Code: Server `moncapro` fehlgeschlagen | Der Server läuft nicht → `moncapro-mcp --http` starten, in `/mcp` neu verbinden |
| "Der MCP-Server braucht das Extra 'mcp'" | `pip install "moncapro[mcp]"` |
| Claude: "Das Projekt wurde inzwischen von einem anderen Client … ersetzt" | Ein anderer Client hat das Projekt ersetzt. Claude prüft mit `get_overview` und fragt nach; das alte Projekt liegt im Backup-Ordner |
| eigene Erweiterung stört die stdio-Verbindung | Im stdio-Modus nie auf stdout `print()`en – nach stderr oder ins Log schreiben |

## Test

```bash
python -m pytest tests/test_api.py                            # API, MCP-Werkzeuge, Revision/Konflikt, Port-Sperre
npx @modelcontextprotocol/inspector                           # Werkzeuge ausprobieren: URL http://127.0.0.1:8765/mcp
```
