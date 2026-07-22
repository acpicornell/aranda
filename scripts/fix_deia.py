#!/usr/bin/env python3
"""One-off correction: the RAH-43 entry (page-097) is DEIA, not a second Sant Joan.

INE's facsimile faithfully prints this sufragania under its parish title
"SAN JUAN BAUTISTA" with Cod.Mun. 07050 / Cl.Mapa 07062 (verified against the
page image). The extraction copied those exactly and then mis-derived
name_catalan = "Sant Joan" (the Pla village) instead of "Deia", which dragged the
map placement onto Sant Joan's coordinates. This fixes the identity, gives Deia
its real municipality code (07018) and coordinates, and adopts the IBESTAT gold
figures (total 759) that the name collision had blocked. INE's printed Cod.Mun.
and Cl.Mapa are preserved in a note.
"""
import json
from pathlib import Path
import xlrd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "web" / "data.json"
XLS = ROOT / "data" / "ibestat" / "I101001_7601_ca.xls"
BANDS = [("0-7", 5, 6), ("7-16", 7, 8), ("16-25", 9, 10),
         ("25-40", 11, 12), ("40-50", 13, 14), ("50+", 15, 16)]

def ibestat_deia():
    sh = xlrd.open_workbook(str(XLS)).sheet_by_index(0)
    def num(r, c):
        v = sh.cell_value(r, c)
        return int(v) if isinstance(v, float) else None
    cur = None
    rec = {}
    for r in range(sh.nrows):
        name = str(sh.cell_value(r, 0)).strip()
        estat = str(sh.cell_value(r, 1)).strip()
        if name and not estat:
            cur = name
        elif cur == "Deià" and estat in ("Total", "Fadrins", "Casats"):
            rec[estat] = {"tot": num(r, 2), "h": num(r, 3), "d": num(r, 4),
                          "age": {b: (num(r, ch), num(r, cd)) for b, ch, cd in BANDS}}
            if estat == "Casats":
                break
    return rec

def build_demografia(v):
    T, F, C = v["Total"], v["Fadrins"], v["Casats"]
    by_age = {}
    for b, _, _ in BANDS:
        ch, cd = C["age"][b]; fh, fd = F["age"][b]
        by_age[b] = {"cas_var": ch, "cas_hem": cd, "sol_var": fh, "sol_hem": fd}
    return {"var": T["h"], "hem": T["d"], "global": T["tot"],
            "casados": {"var": C["h"], "hem": C["d"]},
            "solteros": {"var": F["h"], "hem": F["d"]}, "by_age": by_age}

data = json.loads(DATA.read_text())
p = [x for x in data["pueblos"] if x.get("source_page") == "page-097.jpg"][0]
assert p["pueblo_n"] == 43 and p["total_animes"] == 759

v = ibestat_deia()
dem = build_demografia(v)
print("IBESTAT Deia:", dem["global"], dem["var"], dem["hem"])

# --- identity ---
p["name_catalan"] = "Deià"
p["cod_mun_ine"] = "07018"          # real Deia municipality (INE 07018; per IBESTAT)
p["lat"], p["lon"] = 39.74866, 2.64876
# keep name_modern / cl_mapa / rah_page exactly as INE printed them
p["notes"] = ("Deià. INE titles this entry by its parish, 'SAN JUAN BAUTISTA', and "
              "prints Cód.Mun. 07050 / Cl.Mapa 07062 for it (the sufragània of Sant "
              "Joan Baptista de Deià, then dependent on Valldemossa). The modern "
              "municipality is Deià (INE 07018); do not confuse it with the Pla "
              "village of Sant Joan (RAH 42, INE 07049).")

# --- numbers: IBESTAT gold ---
p["demografia"] = dem
p["total_animes"] = dem["global"]
s = sum(c[k] for c in dem["by_age"].values()
        for k in ("cas_var", "cas_hem", "sol_var", "sol_hem"))
p["sum_check"] = {"method": "ibestat", "sum": s, "total": dem["global"], "ok": s == dem["global"]}
conf = p.get("confidence") or {}
conf["name_catalan"] = "corrected (Deià, per RAH-43 header 'de Deya')"
conf["total_animes"] = "gold (IBESTAT)"
conf["by_age_cells"] = "gold (IBESTAT)"
p["confidence"] = conf

# recompute Mallorca headline total
tot = sum(x["total_animes"] for x in data["pueblos"]
          if not x.get("is_aggregate") and x.get("total_animes"))
data["meta"]["totals"]["total_animes"] = tot

DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
print("sum_check:", p["sum_check"])
print("Mallorca total now:", tot)
print("WROTE web/data.json")
