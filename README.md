# ats-mcp

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that gives AI assistants structured access to the [ATS (Advanced Terrestrial Simulator)](https://github.com/amanzi/ats) source tree. It exposes tools for searching C++ source code, exploring Process Kernels and evaluators, browsing regression tests, validating XML input files, and reading documentation — all scoped safely to the ATS repository root.

## What it does

ATS is a large C++ scientific codebase for simulating coupled hydrological processes (subsurface flow, energy transport, surface water, etc.). Navigating its source tree by hand is tedious. `ats-mcp` lets an AI assistant (e.g. Claude) answer questions like:

- "Where is `Richards_PK` implemented?"
- "List all flow Process Kernels."
- "What does the `eos_liquid_water` evaluator do and where is it registered?"
- "Find regression test inputs for overland flow."
- "Show me a demo input for integrated hydrology."
- "Where is `State` defined in Amanzi?"
- "Is this XML input file well-formed?"
- "Search the docs for `surface_water_content`."

## Repository structure

```
ats-mcp/
├── pyproject.toml          # Package metadata and build config (hatchling)
└── src/
    └── ats_mcp/
        ├── __init__.py
        ├── __main__.py     # Entry point: `python -m ats_mcp`
        ├── config.py       # four repo roots (ATS_ROOT, AMANZI_ROOT, …), env var or sibling default
        ├── server.py       # FastMCP server instance; loads all tool modules
        ├── index/
        │   └── file_utils.py   # path-safe file I/O utilities
        └── tools/
            ├── code.py         # search_source, read_ats_file, search_amanzi_source, read_amanzi_file_tool
            ├── demos.py        # search_demo_inputs, read_demo_file
            ├── docs.py         # list_docs, read_doc, search_docs
            ├── evaluators.py   # describe_evaluator, list_constitutive_relations
            ├── pks.py          # list_pks
            └── tests.py        # list_regression_tests, validate_xml_input, search_regression_test_inputs, read_regression_test_input
```

## Available tools

| Tool | Description |
|------|-------------|
| `search_source` | Case-insensitive regex search across ATS C++ source files (`.cc`, `.hh`, `.cpp`, `.h`) |
| `read_ats_file` | Read any file in the ATS repo with optional start line and line count |
| `search_amanzi_source` | Case-insensitive regex search across Amanzi C++ source files |
| `read_amanzi_file_tool` | Read any file in the Amanzi repo with optional start line and line count |
| `list_pks` | List Process Kernel categories and their header files; filter by category (e.g. `flow`, `energy`) |
| `describe_evaluator` | Find an evaluator by its factory key (e.g. `eos_liquid_water`) and show its `RegisteredFactory` registration |
| `list_constitutive_relations` | List constitutive relation modules; filter by subsystem (e.g. `eos`, `flow`) |
| `list_regression_tests` | List regression test input files (XML, CFG, JSON); filter by substring |
| `validate_xml_input` | Parse an ATS XML input file and report well-formedness errors and top-level structure |
| `search_regression_test_inputs` | Search regression test XML inputs by name, category, or content (most up-to-date input syntax) |
| `read_regression_test_input` | Read a regression test XML input file with optional line range |
| `search_demo_inputs` | Search demo input files by name, category, or content (XML, YAML, notebooks, scripts) |
| `read_demo_file` | Read a file from the ATS demos repository with optional line range |
| `list_docs` | List documentation files (`.rst`, `.md`, `.in`) under `docs/` |
| `read_doc` | Read a documentation file with optional line range |
| `search_docs` | Case-insensitive keyword search across documentation files |

## Configuration

The server resolves four repository roots, each configurable via environment variable with a sibling-directory default:

| Variable | Default (relative to `ats-mcp/`) | Purpose |
|----------|-----------------------------------|---------|
| `ATS_ROOT` | `../ats/` | ATS source tree |
| `AMANZI_ROOT` | `../amanzi/` | Amanzi infrastructure source |
| `ATS_REGRESSION_TESTS_ROOT` | `../ats-regression-tests/` | Regression test XML inputs |
| `ATS_DEMOS_ROOT` | `../ats-demos/` | Demo inputs and notebooks |

If your checkouts all live as siblings of `ats-mcp/` (the standard layout), no environment variables are needed. To override any root:

```bash
export ATS_ROOT=/path/to/ats
export AMANZI_ROOT=/path/to/amanzi
export ATS_REGRESSION_TESTS_ROOT=/path/to/ats-regression-tests
export ATS_DEMOS_ROOT=/path/to/ats-demos
```

Only the roots whose tools you use need to be set. For example, if you only use `search_source` and `read_ats_file`, only `ATS_ROOT` matters.

## Installation with Claude

### Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) — fast Python package manager

### Step 1 — Clone this repo

```bash
git clone https://github.com/your-org/ats-mcp.git
cd ats-mcp
```

### Step 2 — Register the server with Claude Code

Use the `claude mcp add` CLI rather than hand-editing config files. Claude Code stores MCP servers in `~/.claude.json` (not `~/.claude/settings.json`), and the CLI picks the correct block automatically.

Pick a scope:

| Scope | Flag | Where it loads |
|-------|------|----------------|
| **user** | `-s user` | Every Claude Code session, regardless of working directory |
| **project** | `-s project` | Only when CWD matches the project the command was run from; stored per-project in `~/.claude.json` |
| **local** | `-s local` | Written to `.mcp.json` in the current repo; travels with the repo via git |

For most users, **user scope** is the right choice — ATS tools should be available anywhere you work:

```bash
claude mcp add ats-mcp -s user \
  -e ATS_ROOT=/absolute/path/to/ats \
  -- uv run --directory /absolute/path/to/ats-mcp python -m ats_mcp
```

The `--` separates `claude mcp add`'s own flags from the command that launches the server. `-e KEY=VALUE` sets environment variables for the server process; omit it if `ATS_ROOT` is already exported in your shell (or if you rely on the sibling-`ats/` default).

> **Gotcha:** If you previously added the server under project scope from a parent directory (e.g. `/Users/you` instead of `/Users/you/code`), it will silently fail to load from subdirectories. Run `claude mcp list` to see what's registered, and re-add with `-s user` if the scope is wrong.

### Step 3 — Verify

```bash
claude mcp list
```

You should see `ats-mcp: ... - ✓ Connected`. Restart any running Claude Code session so the stdio handshake runs with the new config, then ask Claude:

```
List the ATS Process Kernel categories.
```

### Troubleshooting

- **Server missing from `claude mcp list`** — it's registered under a project scope that doesn't match your CWD. Re-add with `-s user`.
- **`✗ Failed to connect`** — run the launch command manually (`uv run --directory /path/to/ats-mcp python -m ats_mcp`) to surface the real error. Common causes: `uv` not on PATH, wrong `--directory`, Python <3.11.
- **Tools appear but return "ATS_ROOT not found"** — either pass `-e ATS_ROOT=...` at registration time, export it in the shell that launches Claude Code, or place an `ats/` checkout as a sibling of `ats-mcp/`.

## Running manually

```bash
uv run python -m ats_mcp
```

This starts the server on stdio, which is the transport Claude expects. Useful for debugging or testing the server outside of Claude.
