"""File system utilities for the ATS MCP server.

Provides safe path resolution, file reading, and regex search,
all scoped to the ATS_ROOT source tree.
"""

from __future__ import annotations

import re
from pathlib import Path

from ats_mcp.config import ATS_ROOT, ATS_REGRESSION_TESTS_ROOT

SOURCE_EXTENSIONS = {".cc", ".hh", ".cpp", ".h", ".py"}


def safe_resolve(relative_path: str) -> Path:
    """Resolve a repo-relative path and guard against traversal attacks.

    Raises ValueError if the resolved path escapes ATS_ROOT.
    """
    target = (ATS_ROOT / relative_path).resolve()
    if not str(target).startswith(str(ATS_ROOT)):
        raise ValueError(f"Path '{relative_path}' escapes the repository root.")
    return target


def safe_resolve_regression(relative_path: str) -> Path:
    """Resolve a path relative to ATS_REGRESSION_TESTS_ROOT.

    Raises ValueError if the resolved path escapes the regression test root.
    """
    target = (ATS_REGRESSION_TESTS_ROOT / relative_path).resolve()
    if not str(target).startswith(str(ATS_REGRESSION_TESTS_ROOT)):
        raise ValueError(f"Path '{relative_path}' escapes the regression test root.")
    return target


def read_file(relative_path: str, start_line: int = 1, max_lines: int = 300) -> str:
    """Read a file within the ATS source tree with optional line bounds.

    Args:
        relative_path: Path relative to ATS_ROOT.
        start_line: First line to return (1-indexed, default 1).
        max_lines: Maximum lines to return (default 300).

    Returns:
        File contents with a header showing the line range.
    """
    target = safe_resolve(relative_path)
    lines = target.read_text(errors="replace").splitlines()
    total = len(lines)
    start = max(0, start_line - 1)
    chunk = lines[start : start + max_lines]
    header = f"// {relative_path}  (lines {start + 1}–{start + len(chunk)} of {total})\n"
    return header + "\n".join(chunk)


def search_files(
    keyword: str,
    directory: str = "src",
    extensions: frozenset[str] = frozenset(SOURCE_EXTENSIONS),
    max_results: int = 80,
) -> list[dict]:
    """Regex search across ATS source files.

    Args:
        keyword: The symbol or text to search for (case-insensitive).
        directory: Subdirectory within ATS_ROOT to search.
        extensions: File extensions to include.
        max_results: Maximum number of matching lines to return.

    Returns:
        List of dicts with keys: file, line, content.
    """
    search_root = safe_resolve(directory)
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    results: list[dict] = []

    for path in sorted(search_root.rglob("*")):
        if path.suffix not in extensions or not path.is_file():
            continue
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue

        rel = path.relative_to(ATS_ROOT)
        for i, line in enumerate(text.splitlines()):
            if pattern.search(line):
                results.append({"file": str(rel), "line": i + 1, "content": line.strip()})
                if len(results) >= max_results:
                    return results

    return results
