"""Emit web/data.json for the static site from the normalized JSONL.

Shape consumed by web/app.js:

    {
      "meta":    { generated_at, source, totals: {...} },
      "pueblos": [ {pueblo_n, name_catalan, name_1768, cod_mun_ine,
                    total_animes, demografia:{...}, exentos:{...},
                    text:{...}, ...}, ... ]
    }

No DuckDB: the dataset is tiny and the normalized JSONL is already the
single source of truth. (The sibling Floridablanca routes through
DuckDB because it has seven interlocking tables; Aranda is one flat
record per pueblo, so a DB adds nothing here.)

Usage:
    uv run scripts/export_web_data.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NORM = ROOT / "data" / "normalized" / "aranda.jsonl"
OUT = ROOT / "web" / "data.json"

SOURCE = (
    "INE (2013) — Censo del Conde de Aranda (1768), edición facsímil. "
    "Tomo VI, Obispado de Mallorca (R.A.H.). Manuscrito de 1773."
)


def main() -> None:
    if not NORM.exists():
        raise SystemExit(f"missing {NORM}; run normalize.py first")
    pueblos = [json.loads(l) for l in NORM.read_text(encoding="utf-8").splitlines()]
    pueblos.sort(key=lambda r: (r["pueblo_n"] or 0))

    # Aggregate rows (e.g. the "Palma. Resumen de las Parroquias" line) repeat
    # population already counted in their component parishes — exclude from sums.
    counted = [p for p in pueblos if not p.get("is_aggregate")]
    total_pop = sum(p["total_animes"] or 0 for p in counted)
    biggest = max(counted, key=lambda p: p["total_animes"] or 0, default=None)
    verified = sum(1 for p in counted
                   if isinstance((p["demografia"] or {}).get("var"), int)
                   and isinstance((p["demografia"] or {}).get("hem"), int)
                   and (p["demografia"]["var"] + p["demografia"]["hem"]) == p["total_animes"])

    payload = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": SOURCE,
            "diocese": "Mallorca",
            "expected_total_pueblos": 55,
            "totals": {
                "pueblos_extracted": len(counted),
                "population_verified": verified,
                "total_animes": total_pop,
                "biggest": {
                    "name": biggest["name_catalan"] or biggest["name_modern"],
                    "pop": biggest["total_animes"],
                } if biggest else None,
            },
        },
        "pueblos": pueblos,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    kb = OUT.stat().st_size / 1024
    print(f"Wrote {OUT.relative_to(ROOT)} ({len(pueblos)} pueblos, {kb:.1f} KB)")


if __name__ == "__main__":
    main()
