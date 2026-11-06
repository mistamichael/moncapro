# Stabilität und öffentliche API

> Teil der [moncapro-Dokumentation](../../README.md#documentation). English: [doc/en/stability.md](../en/stability.md)

moncapro liegt noch unter Version 1.0. Diese Seite legt fest, worauf du dich **ab 1.0** verlassen kannst, was heute
schon öffentlich ist und wie Änderungen angekündigt werden. Jede Änderung steht im
[Änderungsprotokoll](../../CHANGELOG.md) (englisch).

## Versionierung

moncapro folgt der [semantischen Versionierung](https://semver.org/lang/de/) (`HAUPT.NEBEN.PATCH`).

| Version | Bedeutung |
| --- | --- |
| `0.y.z` (jetzt) | Alles darf sich ändern. Ein Bruch erhöht die Nebenversion (0.1 → 0.2), eine Korrektur die Patch-Version. Festlegen mit `moncapro>=0.2,<0.3`. |
| `1.0.0` | Die öffentliche API unten ist ein Versprechen. |
| `1.y.z` | Neue Funktionen und Korrekturen, ohne die öffentliche API zu brechen. Festlegen mit `moncapro>=1,<2`. |
| `2.0.0` | Die einzige Stelle, an der die öffentliche API brechen darf. |

## Die öffentliche API

Öffentlich ist nur das Folgende. Alles andere ist intern, auch wenn es sich importieren lässt.

| Schnittstelle | Was dazu gehört |
| --- | --- |
| **Python** | Die Namen in `moncapro.__all__` (zum Beispiel `load_project`, `save_project`, `build_schedule`, `Project`, die Task- und Personen-Modelle, `SCHEMA_VERSION`). `ProjectSession` und `ApiError` aus `moncapro.api`. Die Namen in `moncapro.models.__all__`. Die `get_*_dir()`-Funktionen aus `moncapro.paths`. |
| **Kommandozeile** | Der Befehl `moncapro` mit seinen Optionen (`--project`, `--data-dir`, `--cfg-dir`, `--output-dir`, `--start-date`, `--export`, `--scenarios`, `--scenario`, `--simulate`, `--seed`, `--plotly-cdn`, `--save-baseline`, `--lang`, `--verbose`) und den Exit-Codes (0 = alle Projekte verarbeitet, 1 = mindestens eines fehlgeschlagen). |
| **MCP-Server** | Der Befehl `moncapro-mcp` (`--http`, `--host`, `--port`, `--project`), der Servername `moncapro`, die Werkzeuge und Ressourcen aus der [KI-Schnittstelle](ki-schnittstelle.md) mit ihren Parametern und Ergebnissen. |
| **Projektdatei** | Das JSON-Format laut [Projektformat](projektformat.md), einschließlich `schema_version`. |
| **Konfiguration** | Die Dateinamen und Schlüssel in `cfg/` laut [Konfiguration](config_doc.md) und die Umgebungsvariablen `MONCAPRO_CFG`, `MONCAPRO_DATA`, `MONCAPRO_LOG`, `MONCAPRO_RESULTS`, `MONCAPRO_WORK`. |

**Nicht Teil der API:**
- Das Aussehen der Berichte (Layout der Text-, Markdown-, HTML- und Excel-Dateien, die Diagramme). Es darf sich in
  jeder Version verbessern. Maschinenlesbare Ergebnisse liest du aus dem JSON-Export oder der Python-API.
- Alle anderen Module (zum Beispiel `moncapro.models.leveling`, `moncapro.models.expander`, die `*_export`-Module,
  `moncapro.charts`) und jeder Name, der mit einem Unterstrich beginnt. Sie dürfen sich in jeder Version ändern.
- Log-Meldungen und der Wortlaut von Fehlermeldungen (der Typ der Ausnahme gehört zur API, der Text nicht).

## Welche Änderung braucht welche Version

| Änderung | Version |
| --- | --- |
| Etwas Öffentliches entfernen oder umbenennen, seine Bedeutung ändern, ein neuer Pflichtparameter | Bruch: nächste Nebenversion (vor 1.0), nächste Hauptversion (ab 1.0) |
| Etwas Neues und Optionales (neue Funktion, neues optionales Dateifeld, neues Werkzeug) | Nebenversion |
| Fehlerkorrektur, Dokumentation | Patch |
| Eine Änderung des Projektdatei-Formats, die ältere moncapro-Versionen nicht richtig lesen können | Bruch, und `SCHEMA_VERSION` steigt, siehe unten |

### Format der Projektdatei

Jede Datei trägt `schema_version`. moncapro liest ältere Versionen (es bringt sie beim Laden auf den aktuellen Stand)
und lehnt neuere mit einer klaren Meldung ab. Neue optionale Felder ändern die Version nicht. Eine Datei, die du mit
moncapro 1.x gespeichert hast, kann jede spätere moncapro-Version 1.x lesen. Einzelheiten:
[Projektformat](projektformat.md#format-version).

### Abkündigung (Plan für 1.0)

Ab 1.0 wird ein öffentlicher Name nicht sofort entfernt. Er löst zuerst mindestens eine Nebenversion lang eine
`DeprecationWarning` aus (bei Kommandozeile und MCP-Werkzeugen ein Hinweis in der Ausgabe), wird im
Änderungsprotokoll genannt und erst in der nächsten Hauptversion entfernt.

## Von sproject genutzt

Der Desktop-Editor [sproject](https://github.com/mistamichael/sproject) importiert aus moncapro derzeit mehr als die
öffentliche API: `schedule`, `simulation`, `scenarios`, `report_data`, `exporters`, `charts`, `baseline`,
`time_axis`, `colors`, `durations`, mehrere `models.*`-Module, `api.write_backup` und Teile von `mcp.server`. Diese
Importe sind heute intern. Vor 1.0 wird jeder davon entweder **zur öffentlichen API erklärt** (dokumentiert und
getestet) oder in sproject **ersetzt**. Bis dahin können sie sich mit jeder Nebenversion ändern, und sproject legt
deshalb `moncapro>=0.x,<0.(x+1)` fest.

## Auf dem Weg zu 1.0

| Schritt | Stand |
| --- | --- |
| Öffentliche API festgelegt (diese Seite) | erledigt |
| Format-Version in den Projektdateien | erledigt |
| Änderungsprotokoll | erledigt |
| Mehrere Versionen ohne Bruch der öffentlichen API | offen |
| sproject nutzt nur die öffentliche API | offen |
| Entwicklungsstatus „Beta“ auf PyPI, später „Production/Stable“ | offen |
