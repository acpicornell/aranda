#!/usr/bin/env python3
"""Remove the last leftovers of the abandoned OCR/vision pass from web/data.json.

The `notes` field held free-text transcribed from the illegible 1773 cursive
(confabulated Spanish prose, "[il·legible]" markers, stray numbers). Per the
project rule we do not publish unreliable manuscript readings, so every such
note is dropped. The single genuine EDITORIAL note we authored ourselves — the
Deià identity clarification — is kept (rewritten in Catalan to match the UI).

`parroquia` is a short, largely verifiable identity read from the same cursive.
We keep it, but strip the handful of values with clear OCR garbage: fully
unreadable ones are nulled (omit over guess); a few carry a legible advocation
followed by an unreadable tail, from which only the noise tail is removed.

Run:  nix develop -c python scripts/clean_leftovers.py --write
"""
import argparse
import json
import pathlib

DATA = pathlib.Path(__file__).resolve().parent.parent / "web" / "data.json"

# Genuine editorial notes we authored (verifiable), keyed by pueblo_n. Everything
# else in `notes` is transcription from the illegible cursive and gets removed.
KEEP_NOTES = {
    43: (
        "Deià. L'INE encapçala aquesta entrada amb el nom de la seva parròquia, "
        "«SAN JUAN BAUTISTA», i li assigna Cód.Mun. 07050 / Cl.Mapa 07062 (la "
        "sufragània de Sant Joan Baptista de Deià, aleshores dependent de "
        "Valldemossa). El municipi actual és Deià (INE 07018); no s'ha de "
        "confondre amb el poble de Sant Joan del Pla (RAH 42, INE 07049)."
    ),
}

# Explicit, auditable parroquia fixes. None = unreadable, omit. A string trims an
# illegible tail while keeping the legible advocation already present in the read.
PARROQUIA_FIXES = {
    7: None,                            # was 'Palma... (Massas?)' — unreadable
    12: "San Julián",                   # was 'Julian i Llarens'
    18: "San Juan Bautista",            # was 'San Juan Bautista de Espureñes'
    41: "Nuestra Señora de la Asunción",  # was 'Nra. Sra. Olla Asumpcion de Maria'
    45: "San Pedro Apóstol",            # was 'S. Pere Apostol Macia'
    46: "Santa Eugenia",                # was 'Sta Eugenia anexos'
    47: "Santa Margarita",              # was 'Sta Margarita Macuy'
}

NEW_NUMBERS_SOURCE = (
    "IBESTAT gold standard (2026-07-22) — per-parish figures adopted from "
    "I101001_7601; see data/ibestat/SOURCE.md. The manuscript free-text was "
    "omitted (see prose_note); only numbers and identity are published."
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="write changes in place")
    args = ap.parse_args()

    d = json.loads(DATA.read_text(encoding="utf-8"))

    dropped_notes = 0
    for p in d["pueblos"]:
        n = p["pueblo_n"]
        if "notes" in p:
            if n in KEEP_NOTES:
                p["notes"] = KEEP_NOTES[n]
            elif p.get("notes"):
                dropped_notes += 1
                p["notes"] = None
        if n in PARROQUIA_FIXES:
            p["parroquia"] = PARROQUIA_FIXES[n]

    d["meta"]["numbers_source"] = NEW_NUMBERS_SOURCE

    print(f"notes dropped: {dropped_notes}")
    print(f"notes kept (editorial): {sorted(KEEP_NOTES)}")
    print(f"parroquia fixed: {sorted(PARROQUIA_FIXES)}")

    if args.write:
        DATA.write_text(
            json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
        )
        print(f"wrote {DATA}")
    else:
        print("dry run — pass --write to apply")


if __name__ == "__main__":
    main()
