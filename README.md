# moncapro

Critical path (CPM) project planning with Monte Carlo simulation, scenarios and MCP interface.

[![PyPI](https://img.shields.io/pypi/v/moncapro.svg)](https://pypi.org/project/moncapro/)
[![tests](https://github.com/mistamichael/moncapro/actions/workflows/tests.yml/badge.svg)](https://github.com/mistamichael/moncapro/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/mistamichael/moncapro/blob/main/LICENSE)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)

Projects are plain JSON files. `moncapro` computes the critical path in working days, levels
resources (people, vehicles), respects vacation, part-time work and holidays, compares
what-if scenarios and simulates schedule risk with Monte Carlo runs. An MCP server lets AI
clients (e.g. Claude Code) build and calculate projects through tools.

A desktop editor built on moncapro is [sproject](https://github.com/mistamichael/sproject) (Dear PyGui).

## Installation

```bash
pip install moncapro              # core: model, CPM, leveling, simulation, TXT/JSON/Markdown export
pip install "moncapro[all]"       # + Excel, HTML, SVG, Plotly charts, MCP server
```

Extras: `excel`, `html`, `svg`, `charts`, `mcp`, `all`. Python 3.12 or newer.

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

## Documentation

| Topic | English | Deutsch |
|---|---|---|
| Command line | [doc/en/cli.md](https://github.com/mistamichael/moncapro/blob/main/doc/en/cli.md) | [doc/de/cli.md](https://github.com/mistamichael/moncapro/blob/main/doc/de/cli.md) |
| Project file format | [doc/en/project-format.md](https://github.com/mistamichael/moncapro/blob/main/doc/en/project-format.md) | [doc/de/projektformat.md](https://github.com/mistamichael/moncapro/blob/main/doc/de/projektformat.md) |
| Configuration | [doc/en/configuration.md](https://github.com/mistamichael/moncapro/blob/main/doc/en/configuration.md) | [doc/de/config_doc.md](https://github.com/mistamichael/moncapro/blob/main/doc/de/config_doc.md) |
| AI interface (MCP) | [doc/en/ai-interface.md](https://github.com/mistamichael/moncapro/blob/main/doc/en/ai-interface.md) | [doc/de/ki-schnittstelle.md](https://github.com/mistamichael/moncapro/blob/main/doc/de/ki-schnittstelle.md) |
| Examples | [doc/en/examples.md](https://github.com/mistamichael/moncapro/blob/main/doc/en/examples.md) | [doc/de/examples.md](https://github.com/mistamichael/moncapro/blob/main/doc/de/examples.md) |
| Critical path method, dependency types, actuals and baseline | | [doc/de/critical-path-method.md](https://github.com/mistamichael/moncapro/blob/main/doc/de/critical-path-method.md), [doc/de/dependency_types.md](https://github.com/mistamichael/moncapro/blob/main/doc/de/dependency_types.md), [doc/de/termine-und-ist.md](https://github.com/mistamichael/moncapro/blob/main/doc/de/termine-und-ist.md) |

Pre-computed example results: [doc/result_examples/](https://github.com/mistamichael/moncapro/blob/main/doc/result_examples/README.md).

## Development

```bash
python -m venv .venv && .venv/bin/pip install -e ".[dev]"    # Windows: .venv\Scripts\pip
python -m pytest
```

## License

MIT, see [LICENSE](https://github.com/mistamichael/moncapro/blob/main/LICENSE).
