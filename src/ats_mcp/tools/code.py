"""Tools for searching and reading the ATS source code."""

from __future__ import annotations

from ats_mcp.server import mcp
from ats_mcp.index.file_utils import (
    safe_resolve,
    read_file,
    search_files,
    safe_resolve_amanzi,
    read_amanzi_file,
    search_amanzi_files,
)


@mcp.tool()
def search_source(keyword: str, directory: str = "src") -> str:
    """Search ATS source files for a keyword, class name, or symbol.

    Args:
        keyword: The symbol, class name, or text to search for (case-insensitive).
        directory: Subdirectory to search within the repo (default: 'src').
    """
    try:
        search_root = safe_resolve(directory)
    except ValueError as e:
        return f"Error: {e}"

    if not search_root.is_dir():
        return f"Directory '{directory}' not found under ATS root."

    results = search_files(keyword, directory)

    if not results:
        return f"No matches for '{keyword}'."

    lines = [f"{r['file']}:{r['line']}: {r['content']}" for r in results]
    if len(results) >= 80:
        lines.append("... (result limit reached, narrow your search)")
    return "\n".join(lines)


@mcp.tool()
def read_ats_file(relative_path: str, start_line: int = 1, max_lines: int = 300) -> str:
    """Read a file from the ATS repository.

    Args:
        relative_path: Path relative to the ATS repo root,
                       e.g. 'src/pks/flow/Richards_PK.hh'.
        start_line: First line to return (1-indexed, default 1).
        max_lines: Maximum number of lines to return (default 300).
    """
    try:
        target = safe_resolve(relative_path)
    except ValueError as e:
        return f"Error: {e}"

    if not target.exists():
        return f"File not found: {relative_path}"
    if not target.is_file():
        return f"Not a file: {relative_path}"

    return read_file(relative_path, start_line, max_lines)


@mcp.tool()
def search_amanzi_source(keyword: str, directory: str = "src") -> str:
    """Search Amanzi source files for a keyword, class name, or symbol.

    Args:
        keyword: The symbol, class name, or text to search for (case-insensitive).
        directory: Subdirectory to search within the Amanzi repo (default: 'src').
    """
    try:
        search_root = safe_resolve_amanzi(directory)
    except ValueError as e:
        return f"Error: {e}"

    if not search_root.is_dir():
        return f"Directory '{directory}' not found under Amanzi root."

    results = search_amanzi_files(keyword, directory)

    if not results:
        return f"No matches for '{keyword}' in Amanzi '{directory}'."

    lines = [f"{r['file']}:{r['line']}: {r['content']}" for r in results]
    if len(results) >= 80:
        lines.append("... (result limit reached, narrow your search)")
    return "\n".join(lines)


@mcp.tool()
def read_amanzi_file_tool(relative_path: str, start_line: int = 1, max_lines: int = 300) -> str:
    """Read a file from the Amanzi repository.

    Args:
        relative_path: Path relative to the Amanzi repo root,
                       e.g. 'src/utils/Units.hh'.
        start_line: First line to return (1-indexed, default 1).
        max_lines: Maximum number of lines to return (default 300).
    """
    try:
        target = safe_resolve_amanzi(relative_path)
    except ValueError as e:
        return f"Error: {e}"

    if not target.exists():
        return f"File not found: {relative_path}"
    if not target.is_file():
        return f"Not a file: {relative_path}"

    return read_amanzi_file(relative_path, start_line, max_lines)
