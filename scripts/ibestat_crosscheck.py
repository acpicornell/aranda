#!/usr/bin/env python3
"""Cross-check our Aranda edition (web/data.json) against IBESTAT's independent
tabulation of the same 1768 census (data/ibestat/I101001_7601_ca.xls).

Both are transcriptions of the same INE facsimile (see data/ibestat/SOURCE.md),
so agreement = confidence and disagreement = a cell to re-read against the page
image. For every parish we compare the population Total / homes (males) / dones
(females), and when a total matches but the sex split differs we test whether our
own marital breakdown (casados + solteros per sex) already agrees with IBESTAT —
that signals our *column total* was misread while the detail cells are right (a
mechanically fixable error, e.g. Andratx, Santanyí).

Run under the project's Nix shell (provides python3 + xlrd):

    nix develop -c python scripts/ibestat_crosscheck.py
    # or, with direnv:  python scripts/ibestat_crosscheck.py

Reads:  web/data.json, data/ibestat/I101001_7601_ca.xls
Writes: data/reports/ibestat_crosscheck.txt  (also printed to stdout)
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
REPORT = ROOT / "data" / "reports" / "ibestat_crosscheck.txt"

# Column layout of sheet 01 (0-indexed): 2=Total total, 3=Total homes,
# 4=Total dones, then age bands (homes,dones) pairs we don't need for the
# headline check.
C_TOTAL, C_HOMES, C_DONES = 2, 3, 4


def norm(s: str) -> str:
    """Accent/space/punctuation-insensitive key, with a few known aliases."""
    s = unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]", "", s)
    # IBESTAT sorts articles to the end: "Pobla (sa)" == our "sa Pobla".
    aliases = {"poblasa": "sapobla"}
    return aliases.get(s, s)


def load_ibestat(path: Path) -> dict[str, dict]:
    """Parse the per-parish xls into {parish: {Total/Fadrins/Casats: {total,homes,dones}}}."""
    wb = xlrd.open_workbook(str(path))
    sh = wb.sheet_by_index(0)
    recs: dict[str, dict] = {}
    cur = None
    for r in range(sh.nrows):
        name = str(sh.cell_value(r, 0)).strip()
        estat = str(sh.cell_value(r, 1)).strip()
        if name and not estat and "Població" not in name and name.upper() != "PARRÒQUIES":
            cur = "MALLORCA" if name.upper().startswith("MALLORCA") else name
            recs.setdefault(cur, {})
        elif estat in ("Total", "Fadrins", "Casats") and cur:
            def num(c):
                v = sh.cell_value(r, c)
                return int(v) if isinstance(v, float) else None
            recs[cur][estat] = {"total": num(C_TOTAL), "homes": num(C_HOMES), "dones": num(C_DONES)}
    return recs


def our_records(data: dict) -> tuple[dict[str, dict], dict]:
    """Our per-pueblo numbers, with Palma's 6 parishes summed into one 'Palma'."""
    out: dict[str, dict] = {}
    palma = {"total": 0, "homes": 0, "dones": 0}
    for p in data["pueblos"]:
        if p.get("is_aggregate"):
            continue
        nm = p.get("name_catalan") or p.get("name_modern") or ""
        dem = p.get("demografia") or {}
        cas = dem.get("casados") or {}
        sol = dem.get("solteros") or {}
        rec = {
            "name": nm,
            "total": p.get("total_animes"),
            "homes": dem.get("var"),
            "dones": dem.get("hem"),
            # marital totals per sex (may be None if detail is missing)
            "cas_h": cas.get("var"), "cas_d": cas.get("hem"),
            "sol_h": sol.get("var"), "sol_d": sol.get("hem"),
            "page": p.get("source_page"),
        }
        if nm.startswith("Palma"):
            for k in ("total", "homes", "dones"):
                palma[k] += rec[k] or 0
            continue
        # keep both rows when a name repeats (e.g. the duplicate "Sant Joan")
        out.setdefault(norm(nm), []).append(rec)
    return out, palma


def sumx(*vals):
    if any(v is None for v in vals):
        return None
    return sum(vals)


def main() -> int:
    data = json.loads(DATA.read_text())
    ib = load_ibestat(XLS)
    ours, palma = our_records(data)

    lines: list[str] = []
    def out(s=""):
        lines.append(s)
        print(s)

    out("IBESTAT cross-check — Aranda 1768 vs web/data.json")
    out("(source: data/ibestat/SOURCE.md — independent transcription of the same INE facsimile)")
    out("=" * 78)

    # Keep only real parishes: a data row carries a "Total" sub-record. This drops
    # the sheet's footer/footnote lines ("Font:", "Nota:", "1) …", "Total", …) that
    # sit in column 0 with no marital rows under them. Palma is compared separately.
    ib_keys = {
        norm(k): (k, v)
        for k, v in ib.items()
        if k not in ("MALLORCA", "Palma") and v.get("Total")
    }
    exact, fixable, disagree, gaps, unmatched = [], [], [], [], []

    for key, (ibname, ibv) in sorted(ib_keys.items()):
        T = ibv.get("Total", {})
        rows = ours.get(key, [])
        if not rows:
            unmatched.append(ibname)
            continue
        # pick our row whose total is closest to IBESTAT (handles name collisions)
        row = min(rows, key=lambda r: abs((r["total"] or 0) - (T.get("total") or 0)))
        ot, oh, od = row["total"], row["homes"], row["dones"]
        it, ih, idn = T.get("total"), T.get("homes"), T.get("dones")

        if (ot, oh, od) == (it, ih, idn):
            exact.append(ibname)
            continue

        # total matches but sex split differs → is our marital detail already right?
        note = ""
        if ot == it and (oh != ih or od != idn):
            mh = sumx(row["cas_h"], row["sol_h"])   # our males from marital detail
            md = sumx(row["cas_d"], row["sol_d"])
            if mh == ih and md == idn:
                note = f"  → OUR COLUMN-TOTAL MISREAD: set homes={ih}, dones={idn} (marital detail already matches)"
                fixable.append((ibname, oh, od, ih, idn, row["page"]))
        if oh is None or od is None:
            gaps.append((ibname, ot, it, ih, idn))
        elif not note:
            disagree.append((ibname, ot, oh, od, it, ih, idn, row["page"]))

        out(f"\n{ibname}  [{row['page']}]")
        out(f"    ours : total {ot}  homes {oh}  dones {od}")
        out(f"    IBE  : total {it}  homes {ih}  dones {idn}{note}")

    # ---- Palma (our 6 parishes summed) ----
    P = ib.get("Palma")
    out("\n" + "-" * 78)
    out("Palma (our 6 parishes summed vs IBESTAT single 'Palma'):")
    out(f"    ours : total {palma['total']}  homes {palma['homes']}  dones {palma['dones']}")
    if P:
        out(f"    IBE  : total {P['Total']['total']}  homes {P['Total']['homes']}  dones {P['Total']['dones']}")

    # ---- summary ----
    out("\n" + "=" * 78)
    out(f"EXACT match (total+homes+dones): {len(exact)}")
    out(f"FIXABLE (our column total misread, IBESTAT confirms detail): {len(fixable)}")
    for nm, oh, od, ih, idn, pg in fixable:
        out(f"    • {nm} [{pg}]: homes {oh}→{ih}, dones {od}→{idn}")
    out(f"REAL disagreement (re-read the page image): {len(disagree)}")
    for nm, ot, oh, od, it, ih, idn, pg in disagree:
        out(f"    • {nm} [{pg}]: ours {ot}/{oh}/{od}  vs  IBE {it}/{ih}/{idn}")
    out(f"COMPLETENESS gaps (ours lacks sex split, IBESTAT has it): {len(gaps)}")
    for nm, ot, it, ih, idn in gaps:
        out(f"    • {nm}: total ours {ot} / IBE {it}  → IBE homes {ih}, dones {idn}")
    out(f"UNMATCHED IBESTAT parishes (name mapping): {len(unmatched)}")
    for nm in unmatched:
        out(f"    • {nm}")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n")
    print(f"\n[report written to {REPORT.relative_to(ROOT)}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
