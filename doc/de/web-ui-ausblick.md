# Ausblick: Web-Oberfläche für mehrere Nutzer

Dies ist kein Feature, sondern eine Idee für eine mögliche Weiterentwicklung: eine Browser-Oberfläche,
über die mehrere Personen in einer Firma per URL gemeinsam an einem Projekt arbeiten könnten. Es gibt dazu
noch keine Implementierung – dieses Dokument hält die Architekturüberlegung fest, damit sie bei Bedarf als
Ausgangspunkt dient.

> English version: [doc/en/web-ui-outlook.md](../en/web-ui-outlook.md)

## Motivation

Die heutige Desktop-GUI (sproject, Dear PyGui) ist ein lokales Programm pro Person. Für gemeinsames
Arbeiten mehrerer Personen am selben Projekt über einen zentralen Server wäre eine Browser-Oberfläche
eine zusätzliche, parallele Oberfläche – kein Ersatz für sproject. moncapro selbst bleibt dabei unverändert
("kein GUI-Code hier"): die Web-Oberfläche wäre nur ein weiterer Client der bestehenden
[KI-Schnittstelle](ki-schnittstelle.md).

## Warum das grundsätzlich passt

Die MCP-HTTP-Schnittstelle ist bereits für mehrere gleichzeitige Clients ausgelegt: ein Server hält ein
Projekt, beliebig viele Clients lesen und schreiben darüber (siehe
[Grundidee in ki-schnittstelle.md](ki-schnittstelle.md#grundidee-genau-ein-moncapro-server)). Eine
Web-Oberfläche für mehrere Firmenmitarbeiter wäre architektonisch nur ein weiterer solcher Client –
kein Bruch mit dem bestehenden Modell.

## Grobarchitektur

```text
Browser (Person A)  ─┐
Browser (Person B)  ─┼─ HTTPS ──► Web-Backend ──► moncapro-mcp --http
Browser (Person C)  ─┘            (dünn)           hält DAS Projekt, rechnet build_schedule()
```

- **moncapro-Server** (`moncapro-mcp --http`) bleibt wie heute die einzige Instanz, die das Projekt im
  Speicher hält und rechnet. Läuft zentral auf einem Firmenserver statt auf dem eigenen Rechner.
- **Web-Backend** (z. B. FastAPI/Flask) übersetzt Browser-Anfragen in Aufrufe gegen
  `moncapro.api.ProjectSession` bzw. den MCP-Server. Zusätzliche Aufgabe, die moncapro nicht mitbringt:
  Login/Sitzungen der Browser-Nutzer, Zugriffsrechte (lesen vs. ändern).
- **Frontend im Browser**: Gantt-Ansicht, Tabellen, Formulare; sendet Änderungen, zeigt bei Konflikt eine
  verständliche Meldung.
- **Live-Updates**: Damit alle Beteiligten Änderungen anderer sofort sehen, bräuchte es WebSockets/Server-Sent-Events
  im Web-Backend, die bei jeder erfolgreichen Änderung an alle verbundenen Browser pushen. Das MCP-Protokoll
  selbst ist Request/Response pro Client, kein Pub/Sub – diese Verteilung müsste das Web-Backend übernehmen.

## Mehrbenutzer-Mechanik: schon vorhanden, nicht neu zu bauen

Die bestehende Konfliktlogik in `moncapro.api.ProjectSession` würde unverändert weiterverwendet:

- **Laufende Änderungen** (`patch_project`, `add_task`, `update_task`, …) zählen `revision` hoch; jeder
  Client kann mit `get_revision`/`get_state` prüfen, ob sein Stand noch aktuell ist, und mit
  `replace_project(data, base_revision)` nur dann schreiben, wenn sich der Server-Stand seit dem Lesen nicht
  geändert hat (optimistisches Lock – Serverversion gewinnt).
- **Kompletter Projektwechsel** (`new_project`, `load_project`, `replace_project` ohne `base_revision`)
  erhöht den `generation`-Zähler in `ProjectSession` und sichert den alten Stand vorher automatisch
  (`write_backup()`, siehe [Projektwechsel und Sicherungen](ki-schnittstelle.md#projektwechsel-und-sicherungen)).
  Andere Clients bekommen das bei ihrem nächsten Aufruf gemeldet.
- Im MCP-HTTP-Server erkennt `_client_id(ctx)` jede Verbindung über den `mcp-session-id`-Header; der Server
  merkt sich je Client die zuletzt gesehene `generation` (`src/moncapro/mcp/server.py`). Jeder Browser-Nutzer
  bräuchte im Web-Backend eine eigene, stabile MCP-Session, damit diese Erkennung pro Person funktioniert.

Diese Granularität ist **projekt-/revisionsweit**, nicht pro Task. Arbeiten zwei Personen gleichzeitig an
unterschiedlichen Tasks, sieht die Konfliktprüfung das nicht als getrennte Bereiche – ein Schreibversuch mit
veralteter `revision` wird abgelehnt, auch wenn inhaltlich kein Konflikt besteht. Für grobkörniges,
nacheinander erfolgendes Bearbeiten reicht das; für viele Personen, die dauerhaft gleichzeitig verschiedene
Tasks bearbeiten, würde das häufiger zu "bitte neu laden" führen.

## Was zusätzlich zu bauen wäre

- Benutzer-Authentifizierung und Rollen (wer darf ändern, wer nur lesen) – bringt moncapro nicht mit.
- Live-Verteilung von Änderungen an alle verbundenen Browser (WebSocket/SSE-Layer im Web-Backend).
- Browser-Frontend: Gantt-/Tabellen-Darstellung, Formulare, Konfliktmeldungen nutzerfreundlich anzeigen.
- Ggf. feinere Konfliktauflösung (z. B. pro Task), falls die projektweite Revision in der Praxis zu grob ist.

## Was unverändert bleiben würde

- moncapro selbst (Rechenkern, `build_schedule()`, Exporte, MCP-Werkzeuge) – keine Änderung nötig.
- Der HTTP-Modus des MCP-Servers (`moncapro-mcp --http`) als einzige Serverinstanz.
- Die Revision/Generation-Mechanik zur Konflikterkennung.
