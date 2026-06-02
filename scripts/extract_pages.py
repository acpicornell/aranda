"""Burst the source PDF into individual JPGs, one per page.

Each pueblo of the Aranda 1768 census occupies exactly one PDF page.
By converting pages to JPGs upfront we (a) make the subsequent
LLM-vision extraction trivially batchable and (b) allow re-runs to
hit a cache (skip pages already extracted).

Requires ``pdftoppm`` (poppler). On macOS: ``brew install poppler``.

Usage:
    uv run scripts/extract_pages.py [--first N] [--last N] [--dpi 250]
"""

from __future__ import annotations
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_PDF = ROOT / "data" / "sources" / "tomo6_malaga_mallorca_mondoneo_orihuela_osma.pdf"
PAGES_DIR = ROOT / "data" / "pages"


def main() -> None:
    if shutil.which("pdftoppm") is None:
        sys.exit("pdftoppm not found — install poppler (brew install poppler)")
    if not SOURCE_PDF.exists():
        sys.exit(f"source PDF missing: {SOURCE_PDF}")

    ap = argparse.ArgumentParser()
    ap.add_argument("--first", type=int, default=None, help="first page to extract")
    ap.add_argument("--last",  type=int, default=None, help="last page to extract")
    ap.add_argument("--dpi",   type=int, default=250,
                    help="resolution; 250 is enough for vision LLM")
    args = ap.parse_args()

    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        "pdftoppm", "-jpeg", "-r", str(args.dpi),
        str(SOURCE_PDF),
        str(PAGES_DIR / "page"),
    ]
    if args.first is not None:
        cmd += ["-f", str(args.first)]
    if args.last is not None:
        cmd += ["-l", str(args.last)]
    print("running:", " ".join(cmd))
    subprocess.run(cmd, check=True)

    count = len(list(PAGES_DIR.glob("page-*.jpg")))
    print(f"→ {count} JPG file(s) in {PAGES_DIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
