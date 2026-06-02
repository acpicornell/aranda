"""Run Claude vision over each pueblo page and store structured JSON.

Each PDF page of the Aranda 1768 census holds **one or two** pueblos
stacked vertically. We send the whole page (cropped to its content band
and downscaled to a sane size) and ask the model for a JSON *array* of
pueblo objects, then write one file per pueblo: data/extracted/
pueblo-NNN.json, keyed by the printed order number (``raw_n``).

Correctness is enforced downstream by normalize.py / crosscheck.py:
the model is told to return ``null`` for unreadable cells rather than
guess, and the over-determined table arithmetic flags anything that
doesn't reconcile so it can be re-read.

Authentication: ANTHROPIC_API_KEY from the environment, or a .env at
the project root, or — as a fallback — the sibling Madoz project's
.env (the family shares one key).

Usage:
    uv run scripts/extract_vision.py --first 73 --last 104
    uv run scripts/extract_vision.py --first 73 --last 104 --model claude-sonnet-4-6
"""

from __future__ import annotations
import argparse
import base64
import io
import json
import os
import sys
from pathlib import Path
from typing import Any

try:
    from anthropic import Anthropic
except ImportError:
    sys.exit("Install anthropic: uv add anthropic")
try:
    from PIL import Image
except ImportError:
    sys.exit("Install pillow: uv add pillow")
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

ROOT = Path(__file__).resolve().parent.parent
PAGES_DIR = ROOT / "data" / "pages"
OUT_DIR = ROOT / "data" / "extracted"
PROMPT_PATH = ROOT / "prompts" / "extract_pueblo.md"
PROMPT = PROMPT_PATH.read_text(encoding="utf-8") if PROMPT_PATH.exists() else ""

# Rough per-token prices (USD per token) for the cost meter.
PRICES = {
    "claude-opus-4-8":   (15e-6, 75e-6),
    "claude-sonnet-4-6": (3e-6, 15e-6),
    "claude-haiku-4-5":  (1e-6, 5e-6),
}

CONTENT_FRACTION = 0.82   # drop the (usually blank) bottom of the page
MAX_LONG_EDGE = 1500      # downscale target; keeps the table legible


def ensure_api_key() -> None:
    # Self-contained: only the environment or this project's own .env.
    if os.environ.get("ANTHROPIC_API_KEY"):
        return
    if load_dotenv and (ROOT / ".env").exists():
        load_dotenv(ROOT / ".env")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("No ANTHROPIC_API_KEY — set it in the environment or aranda/.env")


def prep_image(p: Path) -> dict:
    """Crop to the content band and downscale; return an image block."""
    im = Image.open(p).convert("RGB")
    w, h = im.size
    im = im.crop((0, 0, w, int(h * CONTENT_FRACTION)))
    long_edge = max(im.size)
    if long_edge > MAX_LONG_EDGE:
        scale = MAX_LONG_EDGE / long_edge
        im = im.resize((int(im.width * scale), int(im.height * scale)),
                       Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=90)
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/jpeg",
            "data": base64.b64encode(buf.getvalue()).decode("ascii"),
        },
    }


def parse_pueblos(text: str) -> list[dict]:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.lstrip().startswith("json"):
            text = text.lstrip()[4:]
    data = json.loads(text)
    if isinstance(data, dict):
        data = [data]
    return data


def page_n(p: Path) -> int:
    return int(p.stem.split("-")[1])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--first", type=int)
    ap.add_argument("--last", type=int)
    ap.add_argument("--model", default="claude-opus-4-8")
    ap.add_argument("--force", action="store_true",
                    help="re-extract pages even if their pueblos exist")
    args = ap.parse_args()

    ensure_api_key()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    client = Anthropic()

    pages = sorted(PAGES_DIR.glob("page-*.jpg"))
    if args.first is not None:
        pages = [p for p in pages if page_n(p) >= args.first]
    if args.last is not None:
        pages = [p for p in pages if page_n(p) <= args.last]
    if not pages:
        sys.exit(f"no pages in {PAGES_DIR} for the given range")

    in_price, out_price = PRICES.get(args.model, (3e-6, 15e-6))
    spent = 0.0
    n_pueblos = 0

    for p in pages:
        try:
            print(f"→ {p.name}", end=" ", flush=True)
            msg = client.messages.create(
                model=args.model,
                max_tokens=4000,
                system=PROMPT,
                messages=[{
                    "role": "user",
                    "content": [
                        prep_image(p),
                        {"type": "text",
                         "text": f"Extract every pueblo on this Aranda 1768 "
                                 f"page ({p.name}). Return a JSON array."},
                    ],
                }],
            )
            text = msg.content[0].text
            pueblos = parse_pueblos(text)
            u = msg.usage
            cost = u.input_tokens * in_price + u.output_tokens * out_price
            spent += cost
            wrote = []
            for ex in pueblos:
                rn = ex.get("raw_n")
                if rn is None:
                    print(f"\n  ⚠ pueblo with no raw_n on {p.name}; skipped")
                    continue
                rec = {
                    "source_page": p.name,
                    "pueblo_n": rn,
                    "model": args.model,
                    "usage": {"input_tokens": u.input_tokens,
                              "output_tokens": u.output_tokens},
                    "extracted": ex,
                }
                out = OUT_DIR / f"pueblo-{int(rn):03d}.json"
                if out.exists() and not args.force:
                    wrote.append(f"{rn}(skip)")
                    continue
                out.write_text(json.dumps(rec, ensure_ascii=False, indent=2),
                               encoding="utf-8")
                wrote.append(str(rn))
                n_pueblos += 1
            print(f"[{', '.join(wrote)}] "
                  f"({u.input_tokens}+{u.output_tokens} tok, ${cost:.3f})")
        except Exception as e:
            print(f"FAIL: {e}")

    print(f"\n{n_pueblos} pueblo file(s) written. Session cost: ${spent:.2f}")


if __name__ == "__main__":
    main()
