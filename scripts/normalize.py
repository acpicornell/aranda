"""Flatten per-pueblo extraction JSON into a sibling-compatible JSONL.

Reads every ``data/extracted/pueblo-NNN.json`` (the output of
``extract_vision.py``), normalises it into one flat record per pueblo,
attaches the modern Catalan toponym, and runs the Σ-against-total
sanity check on the age table. Writes ``data/normalized/aranda.jsonl``.

The modern Catalan name and coordinates come from a self-contained geo
table (``data/geo/mallorca_municipis.json``), baked once from the public
NGIB gazetteer and stored inside this project — no runtime dependency on
sibling projects. Unknown codes fall back to the INE-printed caps name,
title-cased, and are reported so they can be added.

Usage:
    uv run scripts/normalize.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTRACTED = ROOT / "data" / "extracted"
OUT_DIR = ROOT / "data" / "normalized"
OUT = OUT_DIR / "aranda.jsonl"

# Self-contained geo table: cod_mun_ine -> {name_catalan, lat, lon}.
# Baked once from the public NGIB gazetteer and stored INSIDE this project
# (data/geo/) — the pipeline has no runtime dependency on sibling projects.
GEO_PATH = ROOT / "data" / "geo" / "mallorca_municipis.json"
GEO = json.loads(GEO_PATH.read_text(encoding="utf-8"))["municipis"] \
    if GEO_PATH.exists() else {}

AGE_GROUPS = ["0-7", "7-16", "16-25", "25-40", "40-50", "50+"]


def sum_by_age(by_age: dict | None) -> int | None:
    """Σ of every readable cell in the age table, or None if absent."""
    if not by_age:
        return None
    total = 0
    seen = False
    for g in AGE_GROUPS:
        cell = by_age.get(g) or {}
        for k in ("cas_var", "cas_hem", "sol_var", "sol_hem"):
            v = cell.get(k)
            if isinstance(v, int):
                total += v
                seen = True
    return total if seen else None


def normalize_one(rec: dict) -> dict:
    ex = rec["extracted"]
    cod = ex.get("cod_mun_ine")
    geo = GEO.get(cod) or {}
    name_modern = ex.get("name_modern") or ""
    name_catalan = geo.get("name_catalan") or name_modern.title() or None
    lat, lon = geo.get("lat"), geo.get("lon")

    by_age = ex.get("by_age")
    age_sum = sum_by_age(by_age)
    total = ex.get("total_animes")
    # Σ check: only meaningful when we actually read age cells.
    if age_sum is None:
        sum_check = "no_age_data"
    elif total is None:
        sum_check = "no_total"
    elif age_sum == total:
        sum_check = "ok"
    else:
        sum_check = f"mismatch(Σ={age_sum} vs total={total})"

    return {
        "pueblo_n": rec.get("pueblo_n") or ex.get("raw_n"),
        "source_page": rec.get("source_page"),
        "is_aggregate": bool(ex.get("is_resumen")),
        "cifras_stamp": bool(ex.get("cifras_stamp")),
        "cod_mun_ine": cod,
        "cl_mapa": ex.get("cl_mapa"),
        "rah_page": ex.get("rah_page"),
        "name_1768": ex.get("name_1768"),
        "name_modern": name_modern,
        "name_catalan": name_catalan,
        "lat": lat,
        "lon": lon,
        "obispado": ex.get("obispado"),
        "provincia": ex.get("provincia"),
        "parroquia": ex.get("parroquia") or None,
        "total_animes": total,
        "demografia": {
            "var": (ex.get("totals_row") or {}).get("var"),
            "hem": (ex.get("totals_row") or {}).get("hem"),
            "global": (ex.get("totals_row") or {}).get("global"),
            "casados": ex.get("casados_total"),
            "solteros": ex.get("solteros_total"),
            "by_age": by_age,
        },
        "exentos": ex.get("exentos"),
        "text": {
            "eclesiasticos": ex.get("eclesiasticos") or None,
            "conventos_religiosos": ex.get("conventos_religiosos") or None,
            "hospicios_expositos": ex.get("hospicios_expositos") or None,
            "juzgados": ex.get("juzgados") or None,
            "estudios": ex.get("estudios") or None,
            "administraciones_rentas": ex.get("administraciones_rentas") or None,
            "hermitas": ex.get("hermitas") or None,
            "barrios_aldeas": ex.get("barrios_aldeas") or None,
        },
        "cura_relacion_date": ex.get("cura_relacion_date"),
        "notes": ex.get("notes") or None,
        "confidence": ex.get("confidence"),
        "sum_check": sum_check,
    }


def main() -> None:
    files = sorted(EXTRACTED.glob("pueblo-*.json"))
    if not files:
        raise SystemExit(
            f"no extraction files in {EXTRACTED}; run extract_vision.py first"
        )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    uncurated = []
    for f in files:
        rec = json.loads(f.read_text(encoding="utf-8"))
        norm = normalize_one(rec)
        records.append(norm)
        if norm["cod_mun_ine"] not in GEO:
            uncurated.append((norm["cod_mun_ine"], norm["name_modern"]))

    records.sort(key=lambda r: (r["pueblo_n"] or 0))
    with OUT.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"→ {OUT.relative_to(ROOT)} ({len(records)} pueblos)")
    bad = [r for r in records if r["sum_check"].startswith("mismatch")]
    if bad:
        print(f"  ⚠ {len(bad)} pueblo(s) with Σ≠total — see verify_totals.py")
    if uncurated:
        print(f"  ⚠ {len(uncurated)} code(s) without a curated Catalan name "
              f"(fell back to title-case): {uncurated}")


if __name__ == "__main__":
    main()
