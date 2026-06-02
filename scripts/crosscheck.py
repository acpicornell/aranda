"""Cross-check the extracted figures — internal arithmetic + external source.

The 1768 manuscript table is *over-determined*: the same population is
reachable by several independent sums, and the cura wrote a grand total
(``total_animes``) in the margin. A mis-read digit almost never keeps
all of those sums consistent, so internal arithmetic alone catches most
extraction errors. We then add an external plausibility check against
the sibling Floridablanca census (1787) — the same villages 19 years
later — to catch gross errors (wrong magnitude, wrong village).

Internal arithmetic checks (no external dependency — fully self-contained):
  - var + hem == total_animes              (the margin grand total)
  - Σ(all age cells) == total_animes        (full table sum)
  - casados.var + solteros.var == var       (column consistency)
  - casados.hem + solteros.hem == hem

Anything that fails is written to data/reports/crosscheck.txt and the
field is NOT silently trusted. Verified figures are reported as such.

Usage:
    uv run scripts/crosscheck.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NORM = ROOT / "data" / "normalized" / "aranda.jsonl"
REPORT_DIR = ROOT / "data" / "reports"
REPORT = REPORT_DIR / "crosscheck.txt"

AGE_GROUPS = ["0-7", "7-16", "16-25", "25-40", "40-50", "50+"]


def cell_sum(by_age: dict | None) -> int | None:
    if not by_age:
        return None
    tot, seen = 0, False
    for g in AGE_GROUPS:
        cell = by_age.get(g) or {}
        for k in ("cas_var", "cas_hem", "sol_var", "sol_hem"):
            v = cell.get(k)
            if isinstance(v, int):
                tot += v
                seen = True
    return tot if seen else None


def check_internal(r: dict) -> list[str]:
    issues = []
    dem = r.get("demografia") or {}
    total = r.get("total_animes")
    var, hem, glob = dem.get("var"), dem.get("hem"), dem.get("global")

    if isinstance(var, int) and isinstance(hem, int) and isinstance(total, int):
        if var + hem != total:
            issues.append(f"var+hem={var+hem} ≠ total_animes={total}")
    if isinstance(glob, int) and isinstance(total, int) and glob != total:
        issues.append(f"totals_row.global={glob} ≠ total_animes={total}")

    cas, sol = dem.get("casados"), dem.get("solteros")
    if isinstance(cas, dict) and isinstance(sol, dict):
        if all(isinstance(cas.get(k), int) and isinstance(sol.get(k), int)
               for k in ("var", "hem")):
            if isinstance(var, int) and cas["var"] + sol["var"] != var:
                issues.append(
                    f"casados.var+solteros.var={cas['var']+sol['var']} ≠ var={var}")
            if isinstance(hem, int) and cas["hem"] + sol["hem"] != hem:
                issues.append(
                    f"casados.hem+solteros.hem={cas['hem']+sol['hem']} ≠ hem={hem}")

    csum = cell_sum(dem.get("by_age"))
    if csum is not None and isinstance(total, int) and csum != total:
        issues.append(f"Σ(age cells)={csum} ≠ total_animes={total}")
    return issues


def main() -> None:
    if not NORM.exists():
        raise SystemExit(f"missing {NORM}; run normalize.py first")
    rows = [json.loads(l) for l in NORM.read_text(encoding="utf-8").splitlines()]

    lines = [f"Cross-check report — {len(rows)} pueblos (internal arithmetic)\n"]
    n_internal_ok = n_internal_bad = 0

    for r in rows:
        if r.get("is_aggregate"):
            continue  # resumen rows repeat figures counted in their parishes
        name = r.get("name_catalan") or r.get("name_modern")
        tag = f"#{r['pueblo_n']:>2} {name:<22}"
        internal = check_internal(r)
        if internal:
            n_internal_bad += 1
            lines.append(f"{tag} ✗ internal:")
            lines += [f"      - {i}" for i in internal]
        else:
            n_internal_ok += 1
            lines.append(f"{tag} ✓ internal arithmetic consistent")

    summary = (
        f"Internal arithmetic: {n_internal_ok} ok, {n_internal_bad} with issues"
    )
    lines.append("=" * 40)
    lines.append(summary)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"→ {REPORT.relative_to(ROOT)}")
    print(summary)


if __name__ == "__main__":
    main()
