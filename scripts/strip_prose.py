#!/usr/bin/env python3
"""Remove the manuscript free-text prose from the Aranda edition.

The rectors' 1768 relations (clergy, courts, hospitals, sufragànies, notable
buildings, etc.) survive only in a badly degraded photocopy (INE 2013 facsimile
of the RAH 1773 copy). Neither a fluent native reader nor an LLM vision pass can
transcribe that cursive reliably: a model produces plausible, confident text that
mixes the few legible words with pattern-completion, i.e. it can silently invent.
Rather than publish possibly wrong readings to the community, we DISCARD the whole
free-text layer and keep only what does not depend on deciphering the cursive:

  kept  — numbers (IBESTAT gold), identity/geography (INE printed codes),
          the "Esentos por" exemption counts (from the hand-verified tables).
  removed — every `text` sub-field (the relations, incl. the recovered `altres`)
            and `cura_relacion_date` (a date read off the same cursive).
            confidence.text_blocks is dropped as no longer meaningful.

Verified structural facts that happened to live in that prose (e.g. which parish
was a sufragània of which) are historically checkable and can be re-added later
as explicit, sourced structured data — not as transcription.

Run:  nix develop -c python scripts/strip_prose.py            # dry run + report
      nix develop -c python scripts/strip_prose.py --write     # apply to data.json
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "web" / "data.json"


def main() -> int:
    write = "--write" in sys.argv[1:]
    data = json.loads(DATA.read_text())
    n_text = n_date = n_conf = 0
    for p in data["pueblos"]:
        if p.pop("text", None) is not None:
            n_text += 1
        if p.get("cura_relacion_date") is not None:
            p["cura_relacion_date"] = None
            n_date += 1
        conf = p.get("confidence")
        if isinstance(conf, dict) and conf.pop("text_blocks", None) is not None:
            n_conf += 1
    data["meta"]["prose_note"] = (
        "The manuscript free-text relations were omitted: the only source is a "
        "badly degraded facsimile that cannot be transcribed reliably, and we do "
        "not publish possibly erroneous readings. Numbers/identity are unaffected.")

    print(f"pueblos with prose removed : {n_text}")
    print(f"cura_relacion_date nulled  : {n_date}")
    print(f"confidence.text_blocks drop: {n_conf}")
    if write:
        DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
        print("WROTE web/data.json")
    else:
        print("dry run — pass --write to apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
