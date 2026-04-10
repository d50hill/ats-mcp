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

from ats_mcp.config import ATS_ROOT

mcp = FastMCP(
    "ats-mcp",
    instructions=(
        "Tools for exploring the ATS (Advanced Terrestrial Simulator) C++ "
        "source tree. ATS_ROOT is currently: " + str(ATS_ROOT)
    ),
)

# When run as `python -m ats_mcp.server`, this module is loaded as __main__.
# Register it under the canonical name so sub-module imports share the same
# mcp singleton rather than creating a second instance.
if __name__ == "__main__":
    sys.modules.setdefault("ats_mcp.server", sys.modules[__name__])

# Import tool modules to trigger @mcp.tool() registration (side-effect imports).
from ats_mcp.tools import code, pks, evaluators, tests, docs  # noqa: E402, F401


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
