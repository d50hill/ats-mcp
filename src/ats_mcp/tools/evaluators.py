"""Tools for discovering evaluators and constitutive relations in ATS."""

from __future__ import annotations

import re

from ats_mcp.server import mcp
from ats_mcp.config import ATS_ROOT


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
    register_pat = re.compile(
        r"(RegisteredFactory|REGISTER_EVALUATOR|RegisteredEvaluatorFactory)",
        re.IGNORECASE,
    )

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
                snippet = "\n".join(
                    f"  {ctx_start + j + 1}: {l}"
                    for j, l in enumerate(lines[ctx_start:ctx_end])
                )
                hits.append(f"=== {rel} ===\n{snippet}")

    if not hits:
        return (
            f"No RegisteredFactory registration found for '{name}'.\n"
            "Try search_source() with a partial name to locate the evaluator class."
        )
    return "\n\n".join(hits[:5])


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
