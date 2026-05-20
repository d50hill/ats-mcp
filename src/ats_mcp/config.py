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

# Path to the Amanzi repository root, configurable via environment variable.
# Falls back to a sibling `amanzi/` directory next to the project root.
AMANZI_ROOT = Path(
    os.environ.get(
        "AMANZI_ROOT",
        Path(__file__).parent.parent.parent.parent / "amanzi",
    )
).resolve()

# Path to the ATS regression test suite, configurable via environment variable.
# Falls back to a sibling `ats-regression-tests/` directory next to the project root.
ATS_REGRESSION_TESTS_ROOT = Path(
    os.environ.get(
        "ATS_REGRESSION_TESTS_ROOT",
        Path(__file__).parent.parent.parent.parent / "ats-regression-tests",
    )
).resolve()

# Path to the ATS demos repository, configurable via environment variable.
# Falls back to a sibling `ats-demos/` directory next to the project root.
ATS_DEMOS_ROOT = Path(
    os.environ.get(
        "ATS_DEMOS_ROOT",
        Path(__file__).parent.parent.parent.parent / "ats-demos",
    )
).resolve()
