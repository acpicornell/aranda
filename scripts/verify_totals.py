"""Audit the age-table cell reads against the printed population total.

For each pueblo where the vision extraction produced an age table, sum
all cells and compare with ``total_animes`` (the large number in the
left margin, which the cura computed by hand in 1768). A mismatch means
either a cell mis-read or — occasionally — an arithmetic slip in the
manuscript itself. These pueblos are the ones worth a second, careful
extraction pass (e.g. with Opus vision).

Reads ``data/normalized/aranda.jsonl``, writes a report to
``data/reports/verify_totals.txt`` and prints a summary.

Usage:
    uv run scripts/verify_totals.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NORM = ROOT / "data" / "normalized" / "aranda.jsonl"
REPORT_DIR = ROOT / "data" / "reports"
REPORT = REPORT_DIR / "verify_totals.txt"


def main() -> None:
    if not NORM.exists():
        raise SystemExit(f"missing {NORM}; run normalize.py first")
    rows = [json.loads(line) for line in NORM.read_text(encoding="utf-8").splitlines()]

    ok, mismatch, no_data = [], [], []
    for r in rows:
        sc = r.get("sum_check", "")
        label = f"#{r['pueblo_n']:>2} {r['name_catalan'] or r['name_modern']:<22}"
        if sc == "ok":
            ok.append(label)
        elif sc.startswith("mismatch"):
            mismatch.append(f"{label} {sc}")
        else:
            no_data.append(f"{label} ({sc})")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append(f"Verify-totals report — {len(rows)} pueblos\n")
    lines.append(f"OK (Σ == total): {len(ok)}")
    lines.append(f"Mismatch:        {len(mismatch)}")
    lines.append(f"No age data:     {len(no_data)}\n")
    if mismatch:
        lines.append("== MISMATCH — re-extract these ==")
        lines.extend(mismatch)
        lines.append("")
    if no_data:
        lines.append("== No age cells extracted (totals_row only) ==")
        lines.extend(no_data)
        lines.append("")
    if ok:
        lines.append("== OK ==")
        lines.extend(ok)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"→ {REPORT.relative_to(ROOT)}")
    print(f"  OK={len(ok)}  mismatch={len(mismatch)}  no_age_data={len(no_data)}")
    for m in mismatch:
        print(f"  ⚠ {m}")


if __name__ == "__main__":
    main()
