"""Tools for browsing regression tests and validating ATS XML input files."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from ats_mcp.server import mcp
from ats_mcp.config import ATS_ROOT, ATS_REGRESSION_TESTS_ROOT
from ats_mcp.index.file_utils import safe_resolve, safe_resolve_regression


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


@mcp.tool()
def search_regression_test_inputs(
    query: str = "",
    category: str = "",
    content_search: str = "",
    include_orig: bool = False,
    max_results: int = 30,
) -> str:
    """Search for input XML files in the ATS regression test suite.

    The regression tests contain the most up-to-date ATS input file examples.
    Use this to find working inputs for specific physics, solvers, or features.

    Args:
        query: Substring to match against file names, e.g. 'infiltration' or 'arctic'.
        category: Filter by category subdirectory, e.g. '02_richards' or 'transport'.
        content_search: Keyword to search for inside the XML content, e.g. 'overland_flow'.
        include_orig: If True, include legacy '*_orig.xml' reference files (default False).
        max_results: Maximum number of matching files to return (default 30).
    """
    if not ATS_REGRESSION_TESTS_ROOT.is_dir():
        return (
            f"Regression test directory not found: {ATS_REGRESSION_TESTS_ROOT}\n"
            "Set ATS_REGRESSION_TESTS_ROOT env var to point at your ats-regression-tests checkout."
        )

    search_root = ATS_REGRESSION_TESTS_ROOT
    if category:
        # Allow partial category match (e.g. 'transport' matches '06_transport')
        matches = [d for d in search_root.iterdir() if d.is_dir() and category.lower() in d.name.lower()]
        if not matches:
            return f"No category directory matching '{category}' found under {search_root}."
        if len(matches) == 1:
            search_root = matches[0]
        # If multiple match, search across all of them by leaving search_root as-is

    name_pattern = re.compile(re.escape(query), re.IGNORECASE) if query else None
    content_pattern = re.compile(re.escape(content_search), re.IGNORECASE) if content_search else None

    results: list[str] = []
    for xml_path in sorted(search_root.rglob("*.xml")):
        if not include_orig and xml_path.stem.endswith("_orig"):
            continue
        rel = xml_path.relative_to(ATS_REGRESSION_TESTS_ROOT)
        rel_str = str(rel)

        if name_pattern and not name_pattern.search(xml_path.stem):
            continue

        if content_pattern:
            try:
                text = xml_path.read_text(errors="replace")
            except OSError:
                continue
            if not content_pattern.search(text):
                continue

        results.append(rel_str)
        if len(results) >= max_results:
            break

    if not results:
        parts = []
        if query:
            parts.append(f"name matching '{query}'")
        if category:
            parts.append(f"category '{category}'")
        if content_search:
            parts.append(f"content matching '{content_search}'")
        desc = " and ".join(parts) if parts else "any criteria"
        return f"No regression test XML files found for {desc}."

    lines = [f"Regression test inputs in {ATS_REGRESSION_TESTS_ROOT}/:"]
    lines += [f"  {r}" for r in results]
    if len(results) == max_results:
        lines.append(f"  (results capped at {max_results}; refine your query to see more)")
    return "\n".join(lines)


@mcp.tool()
def read_regression_test_input(relative_path: str, start_line: int = 1, max_lines: int = 400) -> str:
    """Read the content of a regression test XML input file.

    Use search_regression_test_inputs first to find the right file path.
    The regression tests contain the most up-to-date ATS input examples.

    Args:
        relative_path: Path to the XML file relative to the regression test root,
            e.g. '02_richards/infiltration_fv.xml'.
        start_line: First line to return (1-indexed, default 1).
        max_lines: Maximum lines to return (default 400).
    """
    try:
        target = safe_resolve_regression(relative_path)
    except ValueError as e:
        return f"Error: {e}"

    if not target.exists():
        return f"File not found: {relative_path} (under {ATS_REGRESSION_TESTS_ROOT})"

    lines = target.read_text(errors="replace").splitlines()
    total = len(lines)
    start = max(0, start_line - 1)
    chunk = lines[start : start + max_lines]
    header = f"// {relative_path}  (lines {start + 1}–{start + len(chunk)} of {total})\n"
    return header + "\n".join(chunk)
