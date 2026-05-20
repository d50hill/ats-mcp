"""ATS MCP Server entry point.

Run with:  uv run python -m ats_mcp

Configure in ~/.claude/settings.json:
    {
      "mcpServers": {
        "ats": {
          "command": "uv",
          "args": ["run", "--directory", "/path/to/ats-mcp", "python", "-m", "ats_mcp"]
        }
      }
    }
"""

from __future__ import annotations

import sys

from mcp.server.fastmcp import FastMCP

from ats_mcp.config import ATS_ROOT, AMANZI_ROOT

_INSTRUCTIONS = f"""\
Tools for exploring ATS (Advanced Terrestrial Simulator) and its parent \
framework Amanzi.
  ATS_ROOT:    {ATS_ROOT}  — physics PKs, constitutive relations, executables
  AMANZI_ROOT: {AMANZI_ROOT}  — infrastructure: state, mesh, operators, \
solvers, utils (Units.hh), PK base classes

ATS is built as a sub-repo of Amanzi. ATS source uses bare `#include "Foo.hh"` \
that resolve to Amanzi headers via CMake.

Routing rules:
- `#include "X.hh"` seen in ATS → try search_amanzi_source first
- State, Mesh, Evaluator, Operator, Solver, Units, PK base classes → Amanzi tools
- Richards/overland flow, surface_balance, snow, MPC, transport PKs → ATS tools

Full reference: ats-mcp/docs/ats-amanzi-linkage.md\
"""

mcp = FastMCP("ats-mcp", instructions=_INSTRUCTIONS)

# When run as `python -m ats_mcp.server`, this module is loaded as __main__.
# Register it under the canonical name so sub-module imports share the same
# mcp singleton rather than creating a second instance.
if __name__ == "__main__":
    sys.modules.setdefault("ats_mcp.server", sys.modules[__name__])

# Import tool modules to trigger @mcp.tool() registration (side-effect imports).
from ats_mcp.tools import code, pks, evaluators, tests, docs, demos  # noqa: E402, F401


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
