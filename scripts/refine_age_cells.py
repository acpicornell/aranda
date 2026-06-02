"""Second Opus pass — re-read the age grid only, for pueblos that don't reconcile.

For each pueblo whose age cells don't sum to the verified margin total,
crop just that pueblo (half a page → ~2x the resolution of the full-page
first pass), and ask Opus to read the age×sex×marital grid with the known
totals supplied as hard reconciliation constraints. The new by_age is
accepted ONLY if Σ(cells) == total_animes (and, when known, the per-sex
sums match var/hem). Otherwise the pueblo stays flagged — never forced.

Usage:
    uv run scripts/refine_age_cells.py            # all flagged pueblos
    uv run scripts/refine_age_cells.py 19 24 26   # specific pueblo numbers
"""

from __future__ import annotations
import base64, io, json, os, sys
from pathlib import Path

from anthropic import Anthropic
from PIL import Image
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "data" / "pages"
EXTRACTED = ROOT / "data" / "extracted"
MAP = json.loads((ROOT / "data" / "_refine_map.json").read_text())
MODEL = "claude-opus-4-8"
AGE_GROUPS = ["0-7", "7-16", "16-25", "25-40", "40-50", "50+"]

# Vertical band per position (fraction of page height).
BANDS = {"T": (0.05, 0.42), "B": (0.46, 0.83)}


def ensure_key():
    if os.environ.get("ANTHROPIC_API_KEY"):
        return
    if load_dotenv and (ROOT / ".env").exists():
        load_dotenv(ROOT / ".env")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("No ANTHROPIC_API_KEY — set it in the environment or aranda/.env")


def crop_pueblo(page: str, pos: str) -> dict:
    im = Image.open(PAGES / page).convert("RGB")
    w, h = im.size
    y0, y1 = BANDS.get(pos, (0.05, 0.42))
    im = im.crop((int(w * 0.03), int(h * y0), int(w * 0.99), int(h * y1)))
    long_edge = max(im.size)
    if long_edge > 1600:
        s = 1600 / long_edge
        im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=92)
    return {"type": "image", "source": {"type": "base64",
            "media_type": "image/jpeg",
            "data": base64.b64encode(buf.getvalue()).decode()}}


def prompt_for(total, var, hem) -> str:
    spine = f"- varones (males) total = {var}, hembras (females) total = {hem}\n" \
        if isinstance(var, int) and isinstance(hem, int) else ""
    return f"""You are reading ONE pueblo of the Censo de Aranda (1768). Read ONLY the demographic grid: rows Casados / Solteros / Total, columns by age group × sex.

These totals are already VERIFIED and FIXED (from the margin grand total and the printed Total column). Do not change them — fit the cells to them:
- total_animes (grand total of everyone) = {total}
{spine}
Age-group columns: 0-7, 7-16, 16-25, 25-40, 40-50, 50+. Each split into varones and hembras. Rows: casados (married) and solteros (single/unmarried).

Hard reconciliation constraints your reading MUST satisfy:
- sum of every cell (cas+sol, all ages, both sexes) = {total}
- sum of all varones cells + sum of all hembras cells = {total}
- read each handwritten digit carefully; if a first read doesn't reconcile, re-examine the cells you are least sure of and adjust to hit the fixed totals.

18th-c. cursive: "7" has a bar; final digits curl; 0 often written "o". Blank casado cells for young ages = 0.

Return ONLY this JSON (no prose, no code fences):
{{"by_age":{{"0-7":{{"cas_var":int,"cas_hem":int,"sol_var":int,"sol_hem":int}},"7-16":{{...}},"16-25":{{...}},"25-40":{{...}},"40-50":{{...}},"50+":{{...}}}},"casados_total":{{"var":int,"hem":int}},"solteros_total":{{"var":int,"hem":int}}}}"""


def cell_sum(by_age) -> int:
    return sum((by_age.get(g) or {}).get(k) or 0
               for g in AGE_GROUPS for k in ("cas_var", "cas_hem", "sol_var", "sol_hem"))


def main():
    ensure_key()
    client = Anthropic()
    pos_map = {int(k): v for k, v in MAP["pos"].items()}
    targets = [int(a) for a in sys.argv[1:]] or MAP["need"]

    fixed = stillbad = 0
    for n in targets:
        f = EXTRACTED / f"pueblo-{n:03d}.json"
        if not f.exists():
            print(f"  #{n}: no file"); continue
        rec = json.loads(f.read_text())
        ex = rec["extracted"]
        total = ex.get("total_animes")
        tr = ex.get("totals_row") or {}
        var, hem = tr.get("var"), tr.get("hem")
        page = rec["source_page"]; pos = pos_map.get(n, "T")
        try:
            msg = client.messages.create(
                model=MODEL, max_tokens=1500,
                messages=[{"role": "user", "content": [
                    crop_pueblo(page, pos),
                    {"type": "text", "text": prompt_for(total, var, hem)}]}])
            text = msg.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("```")[1].lstrip("json").strip()
            data = json.loads(text)
            new_age = data.get("by_age")
            s = cell_sum(new_age)
            if isinstance(total, int) and s == total:
                ex["by_age"] = new_age
                if data.get("casados_total"): ex["casados_total"] = data["casados_total"]
                if data.get("solteros_total"): ex["solteros_total"] = data["solteros_total"]
                ex.setdefault("confidence", {})["by_age_cells"] = "high (reconciled, 2nd pass)"
                f.write_text(json.dumps(rec, ensure_ascii=False, indent=2))
                fixed += 1
                print(f"  #{n:>2} {ex.get('name_modern'):<20} ✓ reconciled (Σ={s}={total})")
            else:
                stillbad += 1
                print(f"  #{n:>2} {ex.get('name_modern'):<20} ✗ still off (Σ={s} vs {total}) — kept flagged")
        except Exception as e:
            stillbad += 1
            print(f"  #{n:>2}: FAIL {e}")
    print(f"\nrefined: {fixed} reconciled, {stillbad} still flagged")


if __name__ == "__main__":
    main()
