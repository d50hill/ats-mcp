"""Tools for discovering Process Kernels (PKs) in ATS."""

from __future__ import annotations

from ats_mcp.server import mcp
from ats_mcp.config import ATS_ROOT


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
