"""
MCP server for the ATS (Advanced Terrestrial Simulator) repository.

Exposes tools for code exploration, PK lookup, input validation,
evaluator discovery, and regression-test browsing.

Usage:
    python server.py

Configure in ~/.claude/settings.json:
    {
      "mcpServers": {
        "ats": {
          "command": "python",
          "args": ["/path/to/ats-mcp/server.py"]
        }
      }
    }
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Resolve ATS root — prefer ATS_ROOT env var, fall back to sibling directory
# ---------------------------------------------------------------------------
_DEFAULT_ATS = Path(__file__).parent.parent / "ats"
ATS_ROOT = Path(os.environ.get("ATS_ROOT", _DEFAULT_ATS)).resolve()

mcp = FastMCP(
    "ats-mcp",
    instructions=(
        "Tools for exploring the ATS (Advanced Terrestrial Simulator) C++ "
        "source tree. ATS_ROOT is currently: " + str(ATS_ROOT)
    ),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_resolve(relative_path: str) -> Path:
    """Resolve a repo-relative path and guard against traversal attacks."""
    target = (ATS_ROOT / relative_path).resolve()
    if not str(target).startswith(str(ATS_ROOT)):
        raise ValueError(f"Path '{relative_path}' escapes the repository root.")
    return target


def _read_truncated(path: Path, max_lines: int = 300) -> str:
    text = path.read_text(errors="replace")
    lines = text.splitlines()
    if len(lines) > max_lines:
        return "\n".join(lines[:max_lines]) + f"\n\n[... truncated at {max_lines}/{len(lines)} lines]"
    return text


# ---------------------------------------------------------------------------
# Tool 1 — search source
# ---------------------------------------------------------------------------

@mcp.tool()
def search_source(keyword: str, directory: str = "src") -> str:
    """Search ATS source files for a keyword, class name, or symbol.

    Args:
        keyword: The symbol, class name, or text to search for (case-insensitive).
        directory: Subdirectory to search within the repo (default: 'src').
    """
    search_root = _safe_resolve(directory)
    if not search_root.is_dir():
        return f"Directory '{directory}' not found under ATS root."

    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    extensions = {".cc", ".hh", ".cpp", ".h", ".py"}
    results: list[str] = []

    for path in sorted(search_root.rglob("*")):
        if path.suffix not in extensions or not path.is_file():
            continue
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        matches = [
            (i + 1, line.strip())
            for i, line in enumerate(text.splitlines())
            if pattern.search(line)
        ]
        if matches:
            rel = path.relative_to(ATS_ROOT)
            for lineno, line in matches[:5]:
                results.append(f"{rel}:{lineno}: {line}")
            if len(results) >= 80:
                results.append("... (result limit reached, narrow your search)")
                break

    return "\n".join(results) if results else f"No matches for '{keyword}'."


# ---------------------------------------------------------------------------
# Tool 2 — list PKs
# ---------------------------------------------------------------------------

@mcp.tool()
def list_pks(category: str = "") -> str:
    """List available Process Kernels (PKs) in ATS.

    Args:
        category: Optional filter — e.g. 'flow', 'energy', 'transport', 'mpc'.
                  Leave empty to list all categories.
    """
    pks_dir = ATS_ROOT / "src" / "pks"
    if not pks_dir.is_dir():
        return "src/pks/ not found — is ATS_ROOT set correctly?"

    cats = sorted(p.name for p in pks_dir.iterdir() if p.is_dir())
    if category:
        cats = [c for c in cats if category.lower() in c.lower()]
    if not cats:
        return f"No PK categories matching '{category}'."

    lines = [f"Process Kernels in {ATS_ROOT}/src/pks/:"]
    for cat in cats:
        subdir = pks_dir / cat
        headers = sorted(h.name for h in subdir.rglob("*.hh"))
        lines.append(f"\n  {cat}/")
        for h in headers[:10]:
            lines.append(f"    {h}")
        if len(headers) > 10:
            lines.append(f"    ... ({len(headers) - 10} more .hh files)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 3 — read file
# ---------------------------------------------------------------------------

@mcp.tool()
def read_file(relative_path: str, start_line: int = 1, max_lines: int = 300) -> str:
    """Read a file from the ATS repository.

    Args:
        relative_path: Path relative to the ATS repo root,
                       e.g. 'src/pks/flow/Richards_PK.hh'.
        start_line: First line to return (1-indexed, default 1).
        max_lines: Maximum number of lines to return (default 300).
    """
    try:
        target = _safe_resolve(relative_path)
    except ValueError as e:
        return f"Error: {e}"

    if not target.exists():
        return f"File not found: {relative_path}"
    if not target.is_file():
        return f"Not a file: {relative_path}"

    lines = target.read_text(errors="replace").splitlines()
    total = len(lines)
    start = max(0, start_line - 1)
    chunk = lines[start : start + max_lines]
    header = f"// {relative_path}  (lines {start + 1}–{start + len(chunk)} of {total})\n"
    return header + "\n".join(chunk)


# ---------------------------------------------------------------------------
# Tool 4 — list constitutive relations
# ---------------------------------------------------------------------------

@mcp.tool()
def list_constitutive_relations(subsystem: str = "") -> str:
    """List constitutive relation modules in ATS.

    Args:
        subsystem: Optional filter — e.g. 'eos', 'flow', 'surface', 'column'.
                   Leave empty to list all subsystems.
    """
    cr_dir = ATS_ROOT / "src" / "constitutive_relations"
    if not cr_dir.is_dir():
        return "src/constitutive_relations/ not found."

    subdirs = sorted(p for p in cr_dir.iterdir() if p.is_dir())
    if subsystem:
        subdirs = [s for s in subdirs if subsystem.lower() in s.name.lower()]
    if not subdirs:
        return f"No constitutive-relation subsystems matching '{subsystem}'."

    lines: list[str] = []
    for sub in subdirs:
        headers = sorted(h.name for h in sub.rglob("*.hh"))
        lines.append(f"\n{sub.name}/  ({len(headers)} headers)")
        for h in headers[:8]:
            lines.append(f"  {h}")
        if len(headers) > 8:
            lines.append(f"  ... ({len(headers) - 8} more)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 5 — describe evaluator (via RegisteredFactory macros)
# ---------------------------------------------------------------------------

@mcp.tool()
def describe_evaluator(name: str) -> str:
    """Find an evaluator by its registered factory key and show its declaration.

    ATS uses REGISTER_EVALUATOR / RegisteredFactory macros to wire evaluator
    names to their C++ classes. This tool locates the registration and shows
    the surrounding source context.

    Args:
        name: The evaluator key string, e.g. 'eos_liquid_water' or 'snow_density'.
    """
    src_dir = ATS_ROOT / "src"
    pattern = re.compile(re.escape(name), re.IGNORECASE)
    register_pat = re.compile(r"(RegisteredFactory|REGISTER_EVALUATOR|RegisteredEvaluatorFactory)", re.IGNORECASE)

    hits: list[str] = []
    for path in sorted(src_dir.rglob("*.cc")):
        try:
            lines = path.read_text(errors="replace").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines):
            if pattern.search(line) and register_pat.search(line):
                rel = path.relative_to(ATS_ROOT)
                ctx_start = max(0, i - 2)
                ctx_end = min(len(lines), i + 5)
                snippet = "\n".join(f"  {ctx_start + j + 1}: {l}" for j, l in enumerate(lines[ctx_start:ctx_end]))
                hits.append(f"=== {rel} ===\n{snippet}")

    if not hits:
        return (
            f"No RegisteredFactory registration found for '{name}'.\n"
            "Try search_source() with a partial name to locate the evaluator class."
        )
    return "\n\n".join(hits[:5])


# ---------------------------------------------------------------------------
# Tool 6 — list regression tests
# ---------------------------------------------------------------------------

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

    # Collect .xml or .cfg input files that look like test cases
    tests: list[str] = []
    for ext in ("*.xml", "*.cfg", "*.json"):
        for p in sorted(found_root.rglob(ext)):
            rel = str(p.relative_to(found_root))
            if filter_str.lower() in rel.lower():
                tests.append(rel)

    if not tests:
        msg = f"No test inputs found"
        if filter_str:
            msg += f" matching '{filter_str}'"
        return msg + f" under {found_root.relative_to(ATS_ROOT)}."

    lines = [f"Regression tests in {found_root.relative_to(ATS_ROOT)}/:"]
    lines += [f"  {t}" for t in tests[:60]]
    if len(tests) > 60:
        lines.append(f"  ... ({len(tests) - 60} more)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 7 — validate XML input file
# ---------------------------------------------------------------------------

@mcp.tool()
def validate_xml_input(relative_path: str) -> str:
    """Parse an ATS XML input file and report structural errors.

    Performs well-formedness checking (catches unclosed tags, bad characters,
    etc.) and reports the top-level ParameterList structure.

    Args:
        relative_path: Path to the XML input file, relative to ATS_ROOT.
    """
    try:
        target = _safe_resolve(relative_path)
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
        tag = elem.tag
        name = elem.get("name", "")
        label = f"{tag}" + (f' name="{name}"' if name else "")
        lines = [f"{indent}<{label}>"]
        if depth < max_depth:
            for child in list(elem)[:8]:
                lines.extend(_summarize(child, depth + 1, max_depth))
            if len(elem) > 8:
                lines.append(f"{indent}  ... ({len(elem) - 8} more children)")
        return lines

    summary = _summarize(root)
    return f"Valid XML. Structure of {relative_path}:\n" + "\n".join(summary)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
