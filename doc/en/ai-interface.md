# AI Interface (MCP)

With the AI interface, an AI tool such as Claude Code or Claude Desktop can create projects, build them
from Excel lists or other sources, check, calculate and save them. Python scripts use the same operations
directly.

> Deutsche Fassung: [doc/de/ki-schnittstelle.md](../de/ki-schnittstelle.md)

## Core Idea: Exactly One moncapro Server

```text
Claude Code / Claude Desktop          other clients (e.g. a GUI)
        │  MCP over HTTP                      │  MCP over HTTP
        └──────────────┬──────────────────────┘
                       ▼
        moncapro server  (moncapro-mcp --http, http://127.0.0.1:8765/mcp)
        moncapro.mcp.server → moncapro.api.ProjectSession → holds THE project
                       ▼
        moncapro.models, build_schedule, exporters, scenarios, simulation
```

- **One** server runs and holds **one** project. All clients see the same state – there is no second,
  hidden copy.
- A second server on the same port refuses to start ("Port 8765 ist belegt – läuft schon ein moncapro-Server?").
- The AI reads source data (Excel, PDF, text) itself and transfers it into the project with the tools.
- Every change is validated immediately. Invalid input changes nothing and returns an error message.
- Calculation runs through `build_schedule()` – the same results as the CLI.

## Setup

### 1. Install and start the server

```bash
pip install "moncapro[mcp]"
moncapro-mcp --http                     # HTTP on http://127.0.0.1:8765/mcp
moncapro-mcp --http --port 8766         # another port
moncapro-mcp --http --project FILE      # open a project at startup
moncapro-mcp --help
```

The terminal shows the address; stop with Ctrl+C. The server listens on `127.0.0.1` only and is therefore
reachable from the local machine only. `python -m moncapro.mcp --http` is equivalent.

### 2. Connect Claude Code

```bash
claude mcp add --transport http moncapro http://127.0.0.1:8765/mcp
```

or put a `.mcp.json` into your working folder:

```json
{"mcpServers": {"moncapro": {"type": "http", "url": "http://127.0.0.1:8765/mcp"}}}
```

Start Claude Code in that folder and approve the server `moncapro` once; `/mcp` shows its status. If the
server is not running yet, Claude Code reports the connection as failed – start the server, then reconnect
in `/mcp`. For a different port, change the URL.

### 3. Other clients (optional)

Any MCP client can share the project with Claude. For clients that edit the project interactively, two tools
exist: `get_revision` (cheap change counter) and `get_state` (counter + project + path), plus
`replace_project(data, base_revision)` for writing back. Conflict rule: if the server's revision moved on in the
meantime, the write is rejected – **the server version wins**. The sproject GUI is such a client.

### stdio mode (special case)

`moncapro-mcp` without `--http` starts a server over stdio, e.g. for an MCP client that launches the server
itself, or for tests. Such a server is **private** to that one client. For shared work always use the HTTP
server. In stdio mode never write to stdout – the library's `print()` output is redirected to stderr.

## Quick Start: New Project from an Excel File

1. Start the server: `moncapro-mcp --http`
2. Start Claude Code and check with `/mcp` that `moncapro` is connected.
3. Ask Claude, for example:

   > Read `webshop.xlsx` and build a new moncapro project from it: master data from the sheet "Project",
   > persons and resources from "Team", tasks with dependencies from "Tasks". Assign each task to the
   > responsible person, use min/max as uncertainty and set the deadline 15 Dec 2026 for the go-live.
   > Check the project, calculate it, tell me end date, costs and critical path, simulate 300 runs and
   > save it as `webshop.json`.

Claude reads the Excel file itself and then calls the tools one after another: `new_project`, `upsert_item`
(persons and resources), `add_task` (the response contains the task id), `add_dependency` (predecessor →
successor with these ids), `set_uncertainty`, `update_task` (deadline), `validate`, `calculate`, `simulate`
and `save_project` (relative paths land in the working folder, `$MONCAPRO_WORK`).

Your own Excel files need no fixed format: describe sheets and columns to Claude in the request; Claude asks
if something is unclear.

## Project Switches and Backups

The server holds exactly one project. If it is **replaced as a whole**, the server first backs up the
previous state to `<work folder>/backup/<timestamp>_<project name>.json` (work folder: `$MONCAPRO_WORK`,
default the current directory) and reports the switch:

| Trigger | Message |
| --- | --- |
| `new_project`, `load_project`, `replace_project` without `base_revision` | the response contains `warning` with old/new project and backup path |
| another client replaced the project | the **next** call of the other clients is **not executed** and reports the switch with the backup path; calling again then works |

In addition:

- The server terminal logs every switch (`[moncapro] Projekt ersetzt: …`).
- The project is only replaced if the new data is valid – otherwise nothing changes (no backup).
- A backup is loaded like any project file, e.g. by Claude with `load_project`
  ("Load the latest backup from the backup folder").
- To change the existing project Claude uses `patch_project`, `add_task` etc. – that is not a switch.

## Example Requests to Claude

- "Read `bauplan.xlsx` (columns: no., activity, duration in days, predecessors) and build a moncapro
  project starting on 4 May 2026. Check it, calculate it and save it as `bauplan.json`."
- "Add the persons Anna (mason, 55 €/h) and Ben (carpenter, 60 €/h) to the open project, assign them to the
  matching tasks and tell me how end date and costs change."
- "Add a scenario 'window delivery delay' in which task 7 can start ten days later, and compare it with
  the base plan."
- "Estimate a min/max duration for all tasks and simulate: by when are we 80 % done?"

## Typical AI Workflow

```text
new_project / load_project
  → add_task (per task; the response contains the assigned id)
  → add_dependency (using the ids from add_task)
  → upsert_item (persons, resources) → update_task (assign resources)
  → validate → calculate → save_project
```

For large lists a single call is faster: `patch_project({"tasks": [...]})` or `replace_project({...})`
with the complete project in JSON format (schema: `moncapro://schema`).

## Tools (MCP)

| Tool | Purpose / result |
| --- | --- |
| `new_project`, `load_project` | create / open a project → overview |
| `save_project` | save (relative paths → work folder) → file path |
| `get_overview`, `get_project` | overview or complete JSON |
| `replace_project` | replace the whole project (project switch with backup and `warning`); with `base_revision` only a change of a known state |
| `patch_project` | set top-level fields (bulk build in the existing project, not a switch) |
| `add_task` | create a task → stored task **incl. `id`** (without `id` the next number is assigned) |
| `get_task`, `update_task`, `remove_task` | read, change (`null` removes a field), delete a task |
| `add_dependency`, `remove_dependency` | dependencies EA (default, finish-to-start), AA, EE, AE |
| `set_uncertainty` | `duration_range` and `risk` for the simulation |
| `upsert_item`, `remove_item`, `set_list` | resources, persons, rest periods, scenarios |
| `validate` | unknown references, cycles, calculation errors → list (empty = OK) |
| `calculate` | start, end, critical path, costs, deadline warnings, dates per task |
| `compare_scenarios`, `simulate` | scenario comparison, Monte Carlo |
| `export` | reports (json, txt, md, html, xlsx, …) to `$MONCAPRO_RESULTS` (default `./results`) |
| `list_examples` | example projects as templates |
| `get_revision`, `get_state` | change counter, or counter + project + path (for interactive clients) |

MCP resources: `moncapro://schema` (JSON schema of the project format), `moncapro://examples/<name>`.

## From Python without MCP

For scripts without a server – works on its own project in memory:

```python
from moncapro.api import ProjectSession, ApiError

s = ProjectSession()
s.new_project("Garage", project_start="2026-04-01")
foundation = s.add_task({"name": "Foundation", "duration": "3d"})   # → task id (here 1)
walls = s.add_task({"name": "Walls", "duration": "5d"})
roof = s.add_task({"name": "Roof", "duration": "2d"})
s.add_dependency(foundation, walls)
s.add_dependency(walls, roof)

s.upsert_item("persons", {"id": "P1", "name": "Anna", "role": "Mason", "hourly_rate": 55})
s.upsert_item("resources", {"id": "R1", "type": "person", "person_id": "P1"})
s.update_task(walls, {"resources": ["R1"]})

assert s.validate() == []
result = s.calculate()
print(result["end"], result["total_costs"], [t["name"] for t in result["critical_path"]])
s.save("garage.json")
s.export(["xlsx", "html"])

try:
    s.add_dependency(roof, 99)
except ApiError as e:
    print(e)          # task 99 not found – the project stays unchanged
```

| Method | Returns |
| --- | --- |
| `new_project(name, project_start, unit)` | overview (dict) |
| `load(path)`, `replace_project(data, base_revision=None)`, `patch_project(fields)` | overview (dict) |
| `save(path=None)` | path as text |
| `get_project()`, `overview()`, `list_tasks()`, `schema()` | project JSON, overview, task list, JSON schema |
| `add_task(task)` | **task id** |
| `get_task(id)`, `update_task(id, fields)`, `set_uncertainty(id, …)` | task (dict, normalized, e.g. `"5"` → `"5d"`) |
| `remove_task(id)` | remaining task ids |
| `add_dependency(predecessor, successor, dep_type="EA")`, `remove_dependency(…)` | predecessor task (dict) |
| `upsert_item(field, item)`, `remove_item(field, key)`, `set_list(field, items)` | entry or count |
| `validate()` | list of problems (empty = OK) |
| `calculate(start_date=None)` | dict: `start`, `end`, `duration_days`, `critical_path`, `total_costs`, `deadline_warnings`, `tracking`, `tasks` |
| `export(formats, out_dir=None)` | list of created files |
| `compare_scenarios()`, `simulate(runs, seed)` | table or dict with `summary` and `top_critical` |
| `revision`, `state()` | change counter, or `{"revision", "project", "path"}` |

Errors are raised as `ApiError` (subclass of `ValueError`) with a readable message (in German).

## Troubleshooting

| Problem | Solution |
| --- | --- |
| "Port 8765 ist belegt – läuft schon ein moncapro-Server?" | a server is already running – use it. Otherwise another port: `--port 8766` (then also adjust the client URL) |
| Claude Code: server `moncapro` failed | the server is not running → start `moncapro-mcp --http`, reconnect in `/mcp` |
| "Der MCP-Server braucht das Extra 'mcp'" | `pip install "moncapro[mcp]"` |
| Claude: "Das Projekt wurde inzwischen von einem anderen Client … ersetzt" | another client replaced the project. Claude should check with `get_overview` and ask the user; the old project is in the backup folder |
| own extension breaks the stdio connection | in stdio mode never `print()` to stdout – write to stderr or the log |

## Tests

```bash
python -m pytest tests/test_api.py                            # API, MCP tools, revision/conflict, port lock
npx @modelcontextprotocol/inspector                           # try the tools: URL http://127.0.0.1:8765/mcp
```
