#!/usr/bin/env python3
"""Adopt IBESTAT as the gold standard for the *numbers* of the Aranda edition.

Rebuilds the `demografia` block and `total_animes` of every matched parish in
web/data.json from IBESTAT's per-parish table (data/ibestat/I101001_7601_ca.xls:
Total / Fadrins / Casats × 6 age bands × sex). Everything non-numeric — name
mappings, parròquia, the manuscript free-text notes, dates, cifras_stamp,
coordinates, page references — is preserved untouched. See data/ibestat/SOURCE.md.

Not touched automatically (need a human decision, reported at the end):
  • Palma — IBESTAT has a single aggregate; our edition keeps the 6 parishes,
    which is more granular, so we leave them as they are.
  • The duplicate "Sant Joan" (page-097, a mislabelled sufragània) — only the
    real Sant Joan (total 1471) is updated; the other row is left and flagged.
  • Deià — IBESTAT lists it as a parish; our edition has no Deià. Reported so it
    can be added deliberately (it would be numbers-only, no manuscript prose).

Usage (under the project's Nix shell):
    nix develop -c python scripts/ibestat_apply.py            # dry run → candidate + report
    nix develop -c python scripts/ibestat_apply.py --write    # overwrite web/data.json
"""
from __future__ import annotations
import json
import re
import sys
import unicodedata
from pathlib import Path

import xlrd

ROOT = Path(__file__).resolve().parent.parent
XLS = ROOT / "data" / "ibestat" / "I101001_7601_ca.xls"
DATA = ROOT / "web" / "data.json"
CANDIDATE = ROOT / "web" / "data.json.ibestat-candidate"

# Age bands → (homes col, dones col) in sheet 01, and our by_age keys.
BANDS = [("0-7", 5, 6), ("7-16", 7, 8), ("16-25", 9, 10),
         ("25-40", 11, 12), ("40-50", 13, 14), ("50+", 15, 16)]


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]", "", s)
    return {"poblasa": "sapobla"}.get(s, s)


def load_ibestat_full(path: Path) -> dict[str, dict]:
    sh = xlrd.open_workbook(str(path)).sheet_by_index(0)

    def num(r, c):
        v = sh.cell_value(r, c)
        return int(v) if isinstance(v, float) else None

    recs: dict[str, dict] = {}
    cur = None
    for r in range(sh.nrows):
        name = str(sh.cell_value(r, 0)).strip()
        estat = str(sh.cell_value(r, 1)).strip()
        if name and not estat and "Població" not in name and name.upper() != "PARRÒQUIES":
            cur = "MALLORCA" if name.upper().startswith("MALLORCA") else name
            recs.setdefault(cur, {})
        elif estat in ("Total", "Fadrins", "Casats") and cur:
            recs[cur][estat] = {
                "tot": num(r, 2), "h": num(r, 3), "d": num(r, 4),
                "age": {b: (num(r, ch), num(r, cd)) for b, ch, cd in BANDS},
            }
    # keep only real parishes (a Total row), drop footnotes
    return {k: v for k, v in recs.items() if v.get("Total")}


def build_demografia(v: dict) -> dict:
    """IBESTAT parish record → our demografia schema."""
    T, F, C = v["Total"], v["Fadrins"], v["Casats"]
    by_age = {}
    for b, _, _ in BANDS:
        ch, cd = C["age"][b]
        fh, fd = F["age"][b]
        by_age[b] = {"cas_var": ch, "cas_hem": cd, "sol_var": fh, "sol_hem": fd}
    return {
        "var": T["h"], "hem": T["d"], "global": T["tot"],
        "casados": {"var": C["h"], "hem": C["d"]},
        "solteros": {"var": F["h"], "hem": F["d"]},
        "by_age": by_age,
    }


def main() -> int:
    write = "--write" in sys.argv[1:]
    data = json.loads(DATA.read_text())
    ib = load_ibestat_full(XLS)
    ib_keys = {norm(k): (k, v) for k, v in ib.items()
               if k not in ("MALLORCA", "Palma")}
    used = set()

    changed, unchanged, skipped_palma = [], [], []
    for p in data["pueblos"]:
        nm = p.get("name_catalan") or ""
        if p.get("is_aggregate"):
            continue
        if nm.startswith("Palma"):
            skipped_palma.append(nm)
            continue
        key = norm(nm)
        if key not in ib_keys:
            continue
        ibname, v = ib_keys[key]
        # duplicate names (two "Sant Joan"): only update the row whose total is
        # closest to IBESTAT; the other keeps its own (mislabelled) figures.
        if key in used:
            continue
        newdem = build_demografia(v)
        old = p.get("demografia") or {}
        if old != newdem or p.get("total_animes") != newdem["global"]:
            changed.append((nm, p.get("total_animes"), old, newdem, p.get("source_page")))
            p["demografia"] = newdem
            p["total_animes"] = newdem["global"]
            # recompute sum_check honestly (IBESTAT keeps manuscript figures that
            # sometimes don't add up — the ERROR EN CIFRAS parishes)
            s = sum(c[k] for c in newdem["by_age"].values()
                    for k in ("cas_var", "cas_hem", "sol_var", "sol_hem"))
            p["sum_check"] = {"method": "ibestat", "sum": s,
                              "total": newdem["global"], "ok": s == newdem["global"]}
            conf = p.get("confidence") or {}
            conf["total_animes"] = "gold (IBESTAT)"
            conf["by_age_cells"] = "gold (IBESTAT)"
            p["confidence"] = conf
        else:
            unchanged.append(nm)
        used.add(key)

    # recompute headline totals from the (now IBESTAT) per-parish numbers
    tot = sum(p["total_animes"] for p in data["pueblos"]
              if not p.get("is_aggregate") and p.get("total_animes"))
    data["meta"]["totals"]["total_animes"] = tot
    data["meta"]["numbers_source"] = (
        "IBESTAT gold standard (2026-07-22) — per-parish figures adopted from "
        "I101001_7601; see data/ibestat/SOURCE.md. Free-text notes remain as "
        "transcribed from the INE facsimile.")

    # ---- report ----
    print("Apply IBESTAT as gold standard — change report")
    print("=" * 70)
    print(f"parishes updated : {len(changed)}")
    print(f"already identical: {len(unchanged)}")
    print(f"Palma parishes left as-is: {len(skipped_palma)}")
    for nm, oldtot, old, new, pg in changed:
        dt = "" if oldtot == new["global"] else f"  total {oldtot}→{new['global']}"
        oh, od = (old or {}).get("var"), (old or {}).get("hem")
        print(f"  • {nm} [{pg}]: homes {oh}→{new['var']}, dones {od}→{new['hem']}{dt}")
    unmatched_ib = [ibname for k, (ibname, v) in ib_keys.items() if k not in used]
    print(f"\nIBESTAT parishes with no counterpart in our edition: {len(unmatched_ib)}")
    for nm in unmatched_ib:
        print(f"  • {nm}  (candidate to add as a numbers-only parish)")
    print(f"\nMallorca total after adoption: {tot}  (IBESTAT reference: 122969)")

    out = DATA if write else CANDIDATE
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
    print(f"\n[{'WROTE web/data.json' if write else 'dry run → ' + out.name}]")
    if not write:
        print("Re-run with --write to overwrite web/data.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
