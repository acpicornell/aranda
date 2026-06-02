"""Snapshot the source PDF locally.

The Censo de Aranda 1768 Balearic section lives in Tomo VI of the INE
2013 facsimile edition. The PDF is 42 MB, public domain. Re-runnable
without side effects.

Usage:
    uv run scripts/fetch_sources.py
"""

from __future__ import annotations
import hashlib
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "data" / "sources"
SOURCES.mkdir(parents=True, exist_ok=True)

# Currently only Tomo VI (Mallorca diocese). The next session should
# confirm whether Eivissa-Formentera is in this volume or a different
# one — if a different volume, add it to this dict.
SOURCES_URLS = {
    "tomo6_malaga_mallorca_mondoneo_orihuela_osma.pdf":
        "https://www.ine.es/prodyser/pubweb/censo_aranda/tomo6.pdf",
}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url: str, target: Path) -> None:
    if target.exists():
        print(f"  ✓ {target.name} already present ({target.stat().st_size:,} B)")
        return
    print(f"  ↓ downloading {url}")
    urllib.request.urlretrieve(url, target)
    print(f"  ✓ wrote {target.name} ({target.stat().st_size:,} B)")


def main() -> None:
    print(f"Snapshot of Aranda 1768 source PDF(s):")
    for name, url in SOURCES_URLS.items():
        fetch(url, SOURCES / name)
    manifest = SOURCES / "MANIFEST.txt"
    with manifest.open("w") as f:
        for name in SOURCES_URLS:
            p = SOURCES / name
            f.write(f"{sha256_of(p)}  {name}\n")
    print(f"  → {manifest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
