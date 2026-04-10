"""Configuration for the ATS MCP server."""

import os
from pathlib import Path

# Path to the ATS repository root, configurable via environment variable.
# Falls back to a sibling `ats/` directory next to the project root.
ATS_ROOT = Path(
    os.environ.get(
        "ATS_ROOT",
        Path(__file__).parent.parent.parent.parent / "ats",
    )
).resolve()
