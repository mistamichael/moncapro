# Changelog

All notable changes to moncapro are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), the versioning follows
[Semantic Versioning](https://semver.org/). While the major version is 0, a breaking change raises the minor
version (0.1 → 0.2) and a fix raises the patch version; see [doc/en/stability.md](doc/en/stability.md).

## [Unreleased]

## [0.2.0] - 2026-11-06

### Added
- Milestones: the project field `milestones` (`{id, name, ref, at: start|end, note}`) names a point in time at the
  start or end of a task. They are resolved against the calculated schedule (for loop and instance tasks: first
  start and last end of all cycles), drawn as vertical lines in the Plotly charts, and can be edited through the
  API and the MCP tools (`upsert_item`, `remove_item`, `set_list`); `validate` reports unknown tasks.
- `schema_version` in project files: the format version of the file, currently `1`. It is written as the first
  field when saving. Files without the field (all files created so far) count as version 1 and load as before;
  files with a newer version are rejected with a clear message instead of losing fields silently; older versions
  are migrated on load. Python: `SCHEMA_VERSION`, `SchemaVersionError`, `moncapro.models.migrate_project_data`.
  See [doc/en/project-format.md](doc/en/project-format.md#format-version).
- Stability policy and the definition of the public API: [doc/en/stability.md](doc/en/stability.md).
- English translations of the dependency types, plan vs. actual and the critical path method
  (`doc/en/dependency-types.md`, `doc/en/actuals-and-baseline.md`, `doc/en/critical-path-method.md`).
- This changelog.

### Changed
- **Breaking:** the `mcp` extra now requires `mcp>=2.0` (before: `mcp>=1.26,<2`). The MCP SDK renamed `FastMCP`
  to `MCPServer`; host and port are now passed to `run()`. Install `moncapro[mcp]` again after upgrading.
- MCP server: error messages of `ApiError` are passed on to clients as tool errors. Without this, mcp 2.x
  replaced them by "Error executing tool …" without text.
- MCP server: the protection against concurrent clients now identifies a client by the `mcp-session-id` header.
  With mcp 2.x the previous identification changed on every call, so the protection never triggered.
- `ProjectSession.get_project()` and `get_state()` always include `schema_version`.
- The command line reports a file with a too new format version in one line (exit code 1) instead of a traceback.
- Examples: software_simple was added to the comparison table, the critical path documentation has a node
  diagram that matches the tank example.

## [0.1.1] - 2026-10-27

### Changed
- **Breaking:** minimum Python version raised from 3.10 to 3.12. The CI matrix now tests 3.12 and 3.13.
- README: badges and absolute links, because PyPI does not resolve relative links.
- GitHub Actions updated (checkout v7, setup-python v7, upload-artifact v7, download-artifact v8); Dependabot
  watches `pip` and `github-actions`.

### Added
- Documentation and golden-file tests for scenario comparison and Monte Carlo simulation (example
  `software_simple`, seed 1).
- English version of the examples page.

## [0.1.0] - 2026-10-27

First release. moncapro was split off from the desktop editor [sproject](https://github.com/mistamichael/sproject).

### Added
- Critical path method with calendar (weekends, holidays), dependency types EA/AA/EE/AE, loop and instance tasks.
- Resource leveling with persons, machines, vacation, part-time work and rest breaks; costs; plan vs. actual with a
  baseline.
- Scenarios and Monte Carlo simulation.
- Exports: JSON, TXT, Markdown, HTML, Excel, SVG, Plotly charts.
- Command line `moncapro` and MCP server `moncapro-mcp`.
- Extras `excel`, `html`, `svg`, `charts`, `mcp`, `all`, `dev`; Python 3.10 or newer; `mcp>=1.26,<2`.

[Unreleased]: https://github.com/mistamichael/moncapro/compare/v0.2.0...main
[0.2.0]: https://github.com/mistamichael/moncapro/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/mistamichael/moncapro/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/mistamichael/moncapro/releases/tag/v0.1.0
