"""Tools for browsing regression tests and validating ATS XML input files."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from ats_mcp.server import mcp
from ats_mcp.config import ATS_ROOT
from ats_mcp.index.file_utils import safe_resolve


@mcp.tool()
def list_regression_tests(filter_str: str = "") -> str:
    """List regression test cases available in the ATS testing directory.

    Args:
        filter_str: Optional substring to filter test names, e.g. 'richards' or 'arctic'.
    """
    test_dirs = [
        ATS_ROOT / "testing" / "ats-regression-tests",
        ATS_ROOT / "testing",
    ]
    found_root: Path | None = None
    for d in test_dirs:
        if d.is_dir():
            found_root = d
            break

    if found_root is None:
        return "Regression test directory not found under testing/."

    tests: list[str] = []
    for ext in ("*.xml", "*.cfg", "*.json"):
        for p in sorted(found_root.rglob(ext)):
            rel = str(p.relative_to(found_root))
            if filter_str.lower() in rel.lower():
                tests.append(rel)

    if not tests:
        msg = "No test inputs found"
        if filter_str:
            msg += f" matching '{filter_str}'"
        return msg + f" under {found_root.relative_to(ATS_ROOT)}."

    lines = [f"Regression tests in {found_root.relative_to(ATS_ROOT)}/:"]
    lines += [f"  {t}" for t in tests[:60]]
    if len(tests) > 60:
        lines.append(f"  ... ({len(tests) - 60} more)")
    return "\n".join(lines)


@mcp.tool()
def validate_xml_input(relative_path: str) -> str:
    """Parse an ATS XML input file and report structural errors.

    Performs well-formedness checking (catches unclosed tags, bad characters,
    etc.) and reports the top-level ParameterList structure.

    Args:
        relative_path: Path to the XML input file, relative to ATS_ROOT.
    """
    try:
        target = safe_resolve(relative_path)
    except ValueError as e:
        return f"Error: {e}"

    if not target.exists():
        return f"File not found: {relative_path}"

    try:
        tree = ET.parse(target)
    except ET.ParseError as e:
        return f"XML parse error in {relative_path}:\n  {e}"

    root = tree.getroot()

    def _summarize(elem: ET.Element, depth: int = 0, max_depth: int = 3) -> list[str]:
        indent = "  " * depth
        name = elem.get("name", "")
        label = elem.tag + (f' name="{name}"' if name else "")
        result = [f"{indent}<{label}>"]
        if depth < max_depth:
            for child in list(elem)[:8]:
                result.extend(_summarize(child, depth + 1, max_depth))
            if len(elem) > 8:
                result.append(f"{indent}  ... ({len(elem) - 8} more children)")
        return result

    summary = _summarize(root)
    return f"Valid XML. Structure of {relative_path}:\n" + "\n".join(summary)
