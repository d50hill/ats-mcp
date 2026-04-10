# ats-mcp

An [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) server that gives AI assistants structured access to the [ATS (Advanced Terrestrial Simulator)](https://github.com/amanzi/ats) source tree. It exposes tools for searching C++ source code, exploring Process Kernels and evaluators, browsing regression tests, validating XML input files, and reading documentation — all scoped safely to the ATS repository root.

## What it does

ATS is a large C++ scientific codebase for simulating coupled hydrological processes (subsurface flow, energy transport, surface water, etc.). Navigating its source tree by hand is tedious. `ats-mcp` lets an AI assistant (e.g. Claude) answer questions like:

- "Where is `Richards_PK` implemented?"
- "List all flow Process Kernels."
- "What does the `eos_liquid_water` evaluator do and where is it registered?"
- "Show me regression tests related to arctic permafrost."
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
        ├── config.py       # ATS_ROOT resolution (env var or sibling ats/ dir)
        ├── server.py       # FastMCP server instance; loads all tool modules
        ├── index/
        │   └── file_utils.py   # safe_resolve, read_file, search_files
        └── tools/
            ├── code.py         # search_source, read_ats_file
            ├── pks.py          # list_pks
            ├── evaluators.py   # describe_evaluator, list_constitutive_relations
            ├── tests.py        # list_regression_tests, validate_xml_input
            └── docs.py         # list_docs, read_doc, search_docs
```

## Available tools

| Tool | Description |
|------|-------------|
| `search_source` | Case-insensitive regex search across ATS C++ source files (`.cc`, `.hh`, `.cpp`, `.h`) |
| `read_ats_file` | Read any file in the ATS repo with optional start line and line count |
| `list_pks` | List Process Kernel categories and their header files; filter by category (e.g. `flow`, `energy`) |
| `describe_evaluator` | Find an evaluator by its factory key (e.g. `eos_liquid_water`) and show its `RegisteredFactory` registration |
| `list_constitutive_relations` | List constitutive relation modules; filter by subsystem (e.g. `eos`, `flow`) |
| `list_regression_tests` | List regression test input files (XML, CFG, JSON); filter by substring |
| `validate_xml_input` | Parse an ATS XML input file and report well-formedness errors and top-level structure |
| `list_docs` | List documentation files (`.rst`, `.md`, `.in`) under `docs/` |
| `read_doc` | Read a documentation file with optional line range |
| `search_docs` | Case-insensitive keyword search across documentation files |

## Configuration

The server needs to know where your ATS checkout lives. Set the `ATS_ROOT` environment variable:

```bash
export ATS_ROOT=/path/to/ats
```

If `ATS_ROOT` is not set, the server defaults to a sibling `ats/` directory next to the `ats-mcp` project root (i.e. `../ats/` relative to this repo).

## Installation with Claude

### Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) — fast Python package manager

### Step 1 — Clone this repo

```bash
git clone https://github.com/your-org/ats-mcp.git
cd ats-mcp
```

### Step 2 — Add to Claude's MCP configuration

Edit `~/.claude/settings.json` (Claude Code) or the equivalent settings file for your Claude client, and add an entry under `mcpServers`:

```json
{
  "mcpServers": {
    "ats": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/ats-mcp", "python", "-m", "ats_mcp"],
      "env": {
        "ATS_ROOT": "/absolute/path/to/ats"
      }
    }
  }
}
```

Replace `/absolute/path/to/ats-mcp` with the directory where you cloned this repo, and `/absolute/path/to/ats` with your ATS checkout. The `env` block is optional if `ATS_ROOT` is already set in your shell environment.

### Step 3 — Verify

Start (or restart) Claude Code. The `ats` MCP server should appear in the connected servers list. You can confirm it is working by asking Claude:

```
List the ATS Process Kernel categories.
```

## Running manually

```bash
uv run python -m ats_mcp
```

This starts the server on stdio, which is the transport Claude expects. Useful for debugging or testing the server outside of Claude.
