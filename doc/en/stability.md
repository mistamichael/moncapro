# Stability and Public API

> Part of the [moncapro documentation](../../README.md#documentation). Deutsch: [doc/de/stabilitaet.md](../de/stabilitaet.md)

moncapro is still below version 1.0. This page says what you can rely on **once 1.0 is released**, what is
public already, and how changes are announced. Every change is listed in the [changelog](../../CHANGELOG.md).

## Versioning

moncapro follows [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`).

| Version | Meaning |
| --- | --- |
| `0.y.z` (now) | Anything may change. A breaking change raises the minor version (0.1 → 0.2), a fix raises the patch version. Pin with `moncapro>=0.2,<0.3`. |
| `1.0.0` | The public API below is a promise. |
| `1.y.z` | New features and fixes without breaking the public API. Pin with `moncapro>=1,<2`. |
| `2.0.0` | The only place where the public API may break. |

## The public API

Only the following is public. Everything else is internal, even if it is importable.

| Interface | What belongs to it |
| --- | --- |
| **Python** | The names in `moncapro.__all__` (for example `load_project`, `save_project`, `build_schedule`, `Project`, the task and person models, `SCHEMA_VERSION`). `ProjectSession` and `ApiError` from `moncapro.api`. The names in `moncapro.models.__all__`. The `get_*_dir()` functions of `moncapro.paths`. |
| **Command line** | The command `moncapro` with its options (`--project`, `--data-dir`, `--cfg-dir`, `--output-dir`, `--start-date`, `--export`, `--scenarios`, `--scenario`, `--simulate`, `--seed`, `--plotly-cdn`, `--save-baseline`, `--lang`, `--verbose`) and the exit codes (0 = all projects processed, 1 = at least one failed). |
| **MCP server** | The command `moncapro-mcp` (`--http`, `--host`, `--port`, `--project`), the server name `moncapro`, the tools and resources listed in the [AI interface](ai-interface.md), with their parameters and results. |
| **Project file** | The JSON format as described in the [project format](project-format.md), including `schema_version`. |
| **Configuration** | The file names and keys in `cfg/` as described in the [configuration](configuration.md), and the environment variables `MONCAPRO_CFG`, `MONCAPRO_DATA`, `MONCAPRO_LOG`, `MONCAPRO_RESULTS`, `MONCAPRO_WORK`. |

**Not part of the API:**
- The look of the reports (layout of the text, Markdown, HTML and Excel files, the charts). It may improve in any
  release. Machine-readable results should be read from the JSON export or from the Python API.
- All other modules (for example `moncapro.models.leveling`, `moncapro.models.expander`, the `*_export` modules,
  `moncapro.charts`) and every name that starts with an underscore. They may change in any release.
- Log messages and the wording of error messages (the type of the exception is part of the API, the text is not).

## What changes need a new version

| Change | Version |
| --- | --- |
| Removing or renaming something public, changing its meaning, a new required parameter | breaking: next minor (before 1.0), next major (from 1.0) |
| Something new and optional (a new function, a new optional file field, a new tool) | minor |
| A bug fix, documentation | patch |
| A change of the project file format that older moncapro versions cannot read correctly | breaking, and `SCHEMA_VERSION` rises; see below |

### Project file format

Every file carries `schema_version`. moncapro reads older versions (it migrates them on load) and rejects newer ones
with a clear message. New optional fields do not change the version. A file you saved with moncapro 1.x can
be read by every later moncapro 1.x. Details: [project format](project-format.md#format-version).

### Deprecation (plan for 1.0)

From 1.0, a public name is not removed at once. It first raises a `DeprecationWarning` (or, for the command line
and MCP tools, a hint in the output) for at least one minor release, is mentioned in the changelog, and is removed
in the next major version.

## Used by sproject

The desktop editor [sproject](https://github.com/mistamichael/sproject) currently imports more than the public API
from moncapro: `schedule`, `simulation`, `scenarios`, `report_data`, `exporters`, `charts`, `baseline`, `time_axis`,
`colors`, `durations`, several `models.*` modules, `api.write_backup` and parts of `mcp.server`. These imports are
internal today. Before 1.0, each of them is either **promoted** to the public API (documented and tested) or
**replaced** in sproject. Until then they can change with any minor release, and sproject pins
`moncapro>=0.x,<0.(x+1)` for that reason.

## On the way to 1.0

| Step | Status |
| --- | --- |
| Public API defined (this page) | done |
| Format version in project files | done |
| Changelog | done |
| Several releases without breaking the public API | open |
| sproject uses only the public API | open |
| Development status "Beta" on PyPI, later "Production/Stable" | open |
