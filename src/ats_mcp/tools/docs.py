"""Tools for browsing and reading ATS documentation."""

from __future__ import annotations

from ats_mcp.config import ATS_ROOT
from ats_mcp.server import mcp
from ats_mcp.index.file_utils import safe_resolve, read_file

DOCS_DIR = "docs"
DOC_EXTENSIONS = {".rst", ".in", ".md"}


@mcp.tool()
def list_docs(subdirectory: str = "") -> str:
    """List documentation files available in the ATS docs directory.

    Args:
        subdirectory: Optional path relative to docs/ to narrow the listing,
                      e.g. 'documentation/source/input_spec'.
    """
    base = DOCS_DIR if not subdirectory else f"{DOCS_DIR}/{subdirectory.strip('/')}"
    try:
        search_root = safe_resolve(base)
    except ValueError as e:
        return f"Error: {e}"

    if not search_root.is_dir():
        return f"Directory '{base}' not found under ATS root."

    paths = sorted(
        p for p in search_root.rglob("*")
        if p.is_file() and p.suffix in DOC_EXTENSIONS
    )

    if not paths:
        return f"No documentation files found in '{base}'."

    lines = [str(p.relative_to(ATS_ROOT)) for p in paths]
    return "\n".join(lines)


@mcp.tool()
def read_doc(relative_path: str, start_line: int = 1, max_lines: int = 400) -> str:
    """Read a documentation file from the ATS docs directory.

    Args:
        relative_path: Path relative to the ATS repo root,
                       e.g. 'docs/documentation/source/input_spec/mesh.rst.in'.
        start_line: First line to return (1-indexed, default 1).
        max_lines: Maximum number of lines to return (default 400).
    """
    try:
        target = safe_resolve(relative_path)
    except ValueError as e:
        return f"Error: {e}"

    if not target.exists():
        return f"File not found: {relative_path}"
    if not target.is_file():
        return f"Not a file: {relative_path}"
    if target.suffix not in DOC_EXTENSIONS:
        return (
            f"'{relative_path}' does not appear to be a documentation file "
            f"(expected one of: {', '.join(sorted(DOC_EXTENSIONS))})."
        )

    return read_file(relative_path, start_line, max_lines)


@mcp.tool()
def search_docs(keyword: str, subdirectory: str = "") -> str:
    """Search ATS documentation files for a keyword or phrase.

    Args:
        keyword: Text to search for (case-insensitive).
        subdirectory: Optional path relative to docs/ to narrow the search,
                      e.g. 'documentation/source/input_spec'.
    """
    import re

    base = DOCS_DIR if not subdirectory else f"{DOCS_DIR}/{subdirectory.strip('/')}"
    try:
        search_root = safe_resolve(base)
    except ValueError as e:
        return f"Error: {e}"

    if not search_root.is_dir():
        return f"Directory '{base}' not found under ATS root."

    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    results: list[str] = []
    max_results = 80

    for path in sorted(search_root.rglob("*")):
        if not path.is_file() or path.suffix not in DOC_EXTENSIONS:
            continue
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue

        rel = path.relative_to(ATS_ROOT)
        for i, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                results.append(f"{rel}:{i}: {line.strip()}")
                if len(results) >= max_results:
                    results.append("... (result limit reached, narrow your search)")
                    return "\n".join(results)

    if not results:
        return f"No matches for '{keyword}' in '{base}'."
    return "\n".join(results)
