#!/usr/bin/env python3
"""Apply the hand-verified "Esentos por" values to web/data.json.

The automatic vision pass had mis-aligned the five exempt columns (values
landing one column off, e.g. Real Servicio read as hidalguía). Antoni
re-read every parish table directly from the INE facsimile; his corrected
readings live in exentos_review.csv (column ACTUAL_ref, "hid/serv/hisenda/
croada/inq", with "?" marking a digit he was unsure of). This script parses
that column and writes the values back, then recomputes the Palma aggregate.

Run: python scripts/apply_exentos_review.py --write
"""
import argparse
import csv
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "web" / "data.json"
CSV = ROOT / "exentos_review.csv"
KEYS = ["hidalguia", "real_servic", "real_hacien", "cruzada", "inquisicion"]


def parse_ref(ref):
    parts = (ref.split("/") + ["", "", "", "", ""])[:5]
    out = []
    for x in parts:
        num = re.sub(r"[^0-9]", "", x)
        out.append(int(num) if num else None)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    d = json.loads(DATA.read_text(encoding="utf-8"))
    byn = {p["pueblo_n"]: p for p in d["pueblos"]}

    rows = list(csv.reader(CSV.open(encoding="utf-8"), delimiter=";"))
    ri = rows[0].index("ACTUAL_ref(hid/serv/hisenda/croada/inq)")

    applied = 0
    for r in rows[1:]:
        if not r or not r[0].strip():
            continue
        n = int(r[0])
        vals = parse_ref(r[ri])
        byn[n]["exentos"] = {k: v for k, v in zip(KEYS, vals)}
        applied += 1

    # Recompute the Palma "Resumen" aggregate from its six parishes.
    agg = next((p for p in d["pueblos"] if p.get("is_aggregate")), None)
    if agg:
        parishes = [p for p in d["pueblos"]
                    if not p.get("is_aggregate") and p.get("name_catalan") == "Palma"]
        agg["exentos"] = {
            k: (sum((p["exentos"].get(k) or 0) for p in parishes) or None)
            for k in KEYS
        }
        print("Palma aggregate exentos:", agg["exentos"])

    print(f"applied {applied} parish rows")
    if args.write:
        DATA.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")
        print("wrote", DATA)
    else:
        print("dry run — pass --write")


if __name__ == "__main__":
    main()
