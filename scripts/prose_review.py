#!/usr/bin/env python3
"""Manual prose review of the Aranda edition, ficha by ficha.

Each page image (data/pages/page-NNN.jpg) was re-read at full resolution from
zoomed crops (see scratchpad crop.py) to correct the machine transcription of
the 18th-c cursive and to recover manuscript rows the 8-field schema had dropped
(e.g. "Edificios notables") into a new catch-all field `altres`.

EDITS[pueblo_n] = {field: new_value}. A field set to None is deleted. Reviewed
fichas get confidence.text_blocks bumped. Original-language (Spanish) is kept in
the values, exactly as the other text fields; only the web labels are Catalan.
Illegible stretches stay marked [il·legible] / [resta il·legible].

Run:  nix develop -c python scripts/prose_review.py            # dry run + report
      nix develop -c python scripts/prose_review.py --write     # apply to data.json
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "web" / "data.json"
REVIEWED = "medium (manual review, crop-verified)"

# --- accumulated review edits ---------------------------------------------
EDITS: dict[int, dict[str, str | None]] = {
    1: {  # Alaró — page-073
        "eclesiasticos": "1 Rector, 2 Vicarios, 9 Beneficiados, 3 Ordenados in sacris, "
            "1 ordenado de menores, sacristán y 2 monacillos, 4 campaneros. Dio la "
            "relación el Rector en 20 de [mes il·legible] de 1768.",
        "barrios_aldeas": "Casas y huertas en su circuición. Su sufragánea es la de "
            "Consell (Concell). [resta il·legible]",
        "altres": "[Edificios notables] 1 Castillo llamado de Alaró, en el qual ay un "
            "Oratorio dedicado a Ntra. Sra. del Refugio, con tres sacerdotes titulares "
            "que van expresados.",
    },
    2: {  # Alcúdia — page-074
        "eclesiasticos": "1 Rector ó Párroco; 6 Beneficiados sacerdotes; 1 sacristán y "
            "3 monacillos. Dió la relación el Rector en fines de 1768.",
        "conventos_religiosos": "1 convento de S. Francisco (observantes) con sacerdotes, "
            "2 legos y 2 donados de razón, y un criado; 1 convento de monjas con 1 síndico.",
        "juzgados": "Está governada con un Bayle y 6 regidores; un Escribano Real; "
            "4 Ministros; un Gobernador de la Plaza residente en la Capital de Palma; "
            "un Sargento mayor; un Ayudante de la Plaza.",
        "estudios": "un Capitán de Llaves; un Guarda Almacén; un Subdelegado de "
            "Intendencia; un Comisario de Cruzada.",
        "altres": "[Nota al margen] 1 Comisario de Marina con 82 Marineros Matriculados "
            "y 5 Soldados Milicianos.",
    },
    3: {  # Algaida — page-074. Dense, faded eclesiásticos: only the confident anchors
        # are transcribed; the middle stays [il·legible]. The date-of-relation sentence
        # had been misfiled under conventos, which Algaida (Pla village) has none of.
        "eclesiasticos": "12 Beneficiados incluso el Rector; 1 Vicario; [detall del "
            "clergat parcialment il·legible]. La parroquia comprende el Monte de Randa. "
            "Dió la relación el Rector en 12 de [mes il·legible] de 1768.",
        "conventos_religiosos": None,
        "hospicios_expositos": "3 Demandadores de limosna.",
        "altres": "[Nota al margen, parcialment il·legible] … 2 Curas y 22 Soldados "
            "Milicianos.",
    },
}
# ---------------------------------------------------------------------------

def main() -> int:
    write = "--write" in sys.argv[1:]
    data = json.loads(DATA.read_text())
    by_n = {p.get("pueblo_n"): p for p in data["pueblos"] if not p.get("is_aggregate")}
    touched = 0
    for n, fields in EDITS.items():
        p = by_n.get(n)
        if not p:
            print(f"!! pueblo_n {n} not found"); continue
        t = p.setdefault("text", {})
        for f, v in fields.items():
            old = t.get(f)
            if v is None:
                t.pop(f, None)
            else:
                t[f] = v
            tag = "DEL" if v is None else ("NEW" if not old else "chg")
            print(f"#{n} {p.get('name_catalan')}: {f} [{tag}]")
        conf = p.setdefault("confidence", {})
        conf["text_blocks"] = REVIEWED
        touched += 1
    print(f"\nreviewed fichas in this run: {touched}")
    if write:
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
        print("WROTE web/data.json")
    else:
        print("dry run — pass --write to apply")
    return 0

if __name__ == "__main__":
    sys.exit(main())
