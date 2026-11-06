# Outlook: web UI for multiple users

This is not a feature, but an idea for a possible future development: a browser-based UI that would let
several people in a company work on the same project together via a URL. There is no implementation yet –
this document records the architecture thinking so it can serve as a starting point if the idea is picked up.

> Deutsche Version: [doc/de/web-ui-ausblick.md](../de/web-ui-ausblick.md)

## Motivation

Today's desktop GUI (sproject, Dear PyGui) is a local program per person. For several people working
together on the same project through a central server, a browser UI would be an additional, parallel
interface – not a replacement for sproject. moncapro itself would stay unchanged ("no GUI code here"): the
web UI would just be another client of the existing [AI interface](ai-interface.md).

## Why this fits architecturally

The MCP HTTP interface is already designed for multiple concurrent clients: one server holds one project,
and any number of clients read and write through it (see the
[core idea in ai-interface.md](ai-interface.md#core-idea-exactly-one-moncapro-server)). A web UI for
several colleagues would architecturally just be another such client – not a break from the existing model.

## Rough architecture

```text
Browser (person A)  ─┐
Browser (person B)  ─┼─ HTTPS ──► Web backend ──► moncapro-mcp --http
Browser (person C)  ─┘            (thin)           holds THE project, runs build_schedule()
```

- **moncapro server** (`moncapro-mcp --http`) stays the single instance holding the project in memory and
  computing it, as today – just running centrally on a company server instead of a local machine.
- **Web backend** (e.g. FastAPI/Flask) translates browser requests into calls against
  `moncapro.api.ProjectSession` or the MCP server. Extra responsibility moncapro does not provide: login/
  sessions for browser users, access rights (read vs. edit).
- **Browser frontend**: Gantt view, tables, forms; sends changes, shows a clear message on conflict.
- **Live updates**: for everyone to see others' changes immediately, the web backend would need a
  WebSocket/Server-Sent-Events layer that pushes to all connected browsers on every successful change. The
  MCP protocol itself is request/response per client, not pub/sub – that distribution would be the web
  backend's job.

## Multi-user mechanics: already there, nothing new to build

The existing conflict logic in `moncapro.api.ProjectSession` would be reused unchanged:

- **Incremental changes** (`patch_project`, `add_task`, `update_task`, …) bump `revision`; any client can
  check with `get_revision`/`get_state` whether its view is still current, and write with
  `replace_project(data, base_revision)` only if the server state has not changed since it last read
  (optimistic locking – the server version wins).
- **Full project replacement** (`new_project`, `load_project`, `replace_project` without `base_revision`)
  bumps the `generation` counter in `ProjectSession` and backs up the previous state first automatically
  (`write_backup()`, see [Project Switches and Backups](ai-interface.md#project-switches-and-backups)).
  Other clients are told about it on their next call.
- In the MCP HTTP server, `_client_id(ctx)` identifies each connection via the `mcp-session-id` header; the
  server tracks the last `generation` seen per client (`src/moncapro/mcp/server.py`). Each browser user
  would need a stable, dedicated MCP session in the web backend for this detection to work per person.

This granularity is **project-/revision-wide, not per task**. If two people work on different tasks at the
same time, the conflict check does not see that as separate areas – a write with a stale `revision` is
rejected even if there is no real content conflict. That is fine for coarse-grained, mostly sequential
editing; for many people continuously editing different tasks at the same time, it would mean more frequent
"please reload" situations.

## What would additionally need to be built

- User authentication and roles (who may edit, who may only view) – moncapro does not provide this.
- Live distribution of changes to all connected browsers (WebSocket/SSE layer in the web backend).
- Browser frontend: Gantt/table rendering, forms, user-friendly conflict messages.
- Possibly finer-grained conflict resolution (e.g. per task), if the project-wide revision proves too coarse
  in practice.

## What would stay unchanged

- moncapro itself (the calculation core, `build_schedule()`, exporters, MCP tools) – no change needed.
- The MCP server's HTTP mode (`moncapro-mcp --http`) as the single server instance.
- The revision/generation mechanism for conflict detection.
