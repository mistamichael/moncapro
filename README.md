# moncapro

Critical path (CPM) project planning with Monte Carlo simulation, scenarios and MCP interface.

Projects are plain JSON files. `moncapro` computes the critical path in working days, levels
resources (people, vehicles), respects vacation, part-time work and holidays, compares
what-if scenarios and simulates schedule risk with Monte Carlo runs. An MCP server lets AI
clients (e.g. Claude Code) build and calculate projects through tools.

## Installation

```bash
pip install moncapro              # core: model, CPM, leveling, simulation, TXT/JSON/Markdown export
pip install "moncapro[all]"       # + Excel, HTML, SVG, Plotly charts, MCP server
```

Extras: `excel`, `html`, `svg`, `charts`, `mcp`, `all`. Python 3.10 or newer.

## Quickstart

```python
from moncapro import load_project, build_schedule

project = load_project("my_project.json")
schedule = build_schedule(project)
print(schedule.cpm.project_duration)
```

Command line:

```bash
moncapro --project my_project.json --export json,txt,md
```

MCP server (needs the `mcp` extra):

```bash
moncapro-mcp --http --port 8765
claude mcp add --transport http moncapro http://127.0.0.1:8765/mcp
```

Example projects ship with the package (`moncapro.paths.get_examples_dir()`).

## Configuration

The packaged `cfg/` (working hours, calendar, export layout) is used by default. Override it with
a directory of your own: `--cfg-dir` or `MONCAPRO_CFG`.

| Variable | Meaning | Default |
|---|---|---|
| `MONCAPRO_CFG` | configuration directory | packaged `cfg/` |
| `MONCAPRO_RESULTS` | export output | `./results` |
| `MONCAPRO_WORK` | working files, backups | current directory |
| `MONCAPRO_LOG` | log files | `./log` |
| `MONCAPRO_DATA` | CLI input projects | `./data` |

## License

MIT, see [LICENSE](LICENSE).
