"""Tools for browsing and reading ATS demo examples.

Demos are more complete, realistic examples than regression tests, but their
XML inputs may be outdated relative to the current ATS input spec.  Use the
regression test tools for the most up-to-date input syntax, and demos for
broader context (notebooks, scripts, multi-file setups).
"""

from __future__ import annotations

import re
from pathlib import Path

from ats_mcp.server import mcp
from ats_mcp.config import ATS_DEMOS_ROOT
from ats_mcp.index.file_utils import safe_resolve_demos

# File extensions treated as readable text for search and display.
_TEXT_EXTENSIONS = {".xml", ".yaml", ".yml", ".cfg", ".py", ".ipynb", ".rst", ".txt", ".in"}


@mcp.tool()
def search_demo_inputs(
    query: str = "",
    category: str = "",
    content_search: str = "",
    file_types: str = "xml,yaml",
    max_results: int = 30,
) -> str:
    """Search for input files in the ATS demos repository.

    Demos are realistic, multi-file examples (XML inputs, notebooks, scripts).
    NOTE: Demo XML inputs may be outdated — use search_regression_test_inputs
    for the most current input file syntax.

    Args:
        query: Substring to match against file names, e.g. 'hillslope' or 'permafrost'.
        category: Filter by category subdirectory, e.g. '04_integrated_hydro' or 'arctic'.
        content_search: Keyword to search for inside file contents, e.g. 'overland flow'.
        file_types: Comma-separated extensions to search (default 'xml,yaml').
            Supported: xml, yaml, cfg, py, ipynb, rst, txt, in.
        max_results: Maximum number of matching files to return (default 30).
    """
    if not ATS_DEMOS_ROOT.is_dir():
        return (
            f"Demos directory not found: {ATS_DEMOS_ROOT}\n"
            "Set ATS_DEMOS_ROOT env var to point at your ats-demos checkout."
        )

    # Parse requested extensions
    requested_exts: set[str] = set()
    for ext in file_types.split(","):
        ext = ext.strip().lstrip(".")
        if ext:
            requested_exts.add(f".{ext}")
    allowed_exts = requested_exts & _TEXT_EXTENSIONS
    if not allowed_exts:
        return f"No supported file types in '{file_types}'. Supported: {', '.join(sorted(_TEXT_EXTENSIONS))}."

    search_root = ATS_DEMOS_ROOT
    if category:
        matches = [d for d in search_root.iterdir() if d.is_dir() and category.lower() in d.name.lower()]
        if not matches:
            return f"No category directory matching '{category}' found under {search_root}."
        if len(matches) == 1:
            search_root = matches[0]

    name_pattern = re.compile(re.escape(query), re.IGNORECASE) if query else None
    content_pattern = re.compile(re.escape(content_search), re.IGNORECASE) if content_search else None

    results: list[str] = []
    for path in sorted(search_root.rglob("*")):
        if not path.is_file() or path.suffix not in allowed_exts:
            continue
        rel = path.relative_to(ATS_DEMOS_ROOT)
        rel_str = str(rel)

        if name_pattern and not name_pattern.search(path.stem):
            continue

        if content_pattern:
            try:
                text = path.read_text(errors="replace")
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
        return f"No demo files found for {desc} (types: {file_types})."

    lines = [f"Demo files in {ATS_DEMOS_ROOT}/: (NOTE: XML inputs may be outdated)"]
    lines += [f"  {r}" for r in results]
    if len(results) == max_results:
        lines.append(f"  (results capped at {max_results}; refine your query to see more)")
    return "\n".join(lines)


@mcp.tool()
def read_demo_file(relative_path: str, start_line: int = 1, max_lines: int = 400) -> str:
    """Read a file from the ATS demos repository.

    Use search_demo_inputs first to find the right file path.
    Supports XML, YAML, Python scripts, Jupyter notebooks (.ipynb), and cfg files.
    NOTE: Demo XML inputs may be outdated relative to current ATS input syntax.

    Args:
        relative_path: Path to the file relative to the demos root,
            e.g. '04_integrated_hydro/column.xml' or '06_arctic_hydrology/arctic_hydrology.ipynb'.
        start_line: First line to return (1-indexed, default 1).
        max_lines: Maximum lines to return (default 400).
    """
    try:
        target = safe_resolve_demos(relative_path)
    except ValueError as e:
        return f"Error: {e}"

    if not target.exists():
        return f"File not found: {relative_path} (under {ATS_DEMOS_ROOT})"

    if target.suffix not in _TEXT_EXTENSIONS:
        return (
            f"File '{relative_path}' has extension '{target.suffix}' which is not a readable text file. "
            f"Readable types: {', '.join(sorted(_TEXT_EXTENSIONS))}."
        )

    lines = target.read_text(errors="replace").splitlines()
    total = len(lines)
    start = max(0, start_line - 1)
    chunk = lines[start : start + max_lines]
    note = "  NOTE: Demo XML inputs may be outdated — cross-check with regression tests.\n" if target.suffix == ".xml" else ""
    header = f"// {relative_path}  (lines {start + 1}–{start + len(chunk)} of {total})\n{note}"
    return header + "\n".join(chunk)
