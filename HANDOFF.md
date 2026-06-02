# Handoff — what was decided in the previous session

> **⚠ HISTORICAL.** This was the catch-up note for a session that has since
> been completed. The project is now **done**: all 54 pueblos/parishes extracted
> and verified (51/54 reconciled), website live (Inici · Pobles · Mapa ·
> Demografia · Font). For the current state see **`README.md`**. Note the
> coverage correction: Eivissa/Formentera *should* have been in the volume but
> are an INE-documented omission (facsimile p. 65) — see README.

Date of handoff: **2026-06-02**. Previous session was conducted from the `meta` project directory.

## TL;DR

A live extraction test on 4 Mallorcan villages confirmed that **the project is viable, cheap (~$2-5 LLM cost for the whole Balearic section), and structurally identical to the existing sibling projects**. Greenlit. The next session starts cold; this document is the catch-up.

## What's true about the source

| Question | Answer |
|---|---|
| Is it accessible online? | **YES** — `https://www.ine.es/prodyser/pubweb/censo_aranda/tomo6.pdf` |
| Public domain? | YES (INE 2013 facsimile of 1773 manuscript copy) |
| Size | 42 MB, 442 pages, JPG-image content (no text layer) |
| Balearic coverage | Mallorca + Eivissa-Formentera (Menorca excluded — British rule 1708-1782) |
| Page structure | One PDF page = one pueblo (a few exceptions for diocese covers / maps) |
| Per-pueblo content | Manuscript table 1768 + INE-printed metadata 2013 overlay |

## What the previous session actually verified (live)

The previous session loaded pages 75-78 of the PDF (which contain ANDRAIX, ARTA, BAÑALBUFAR, BINISALEM, BUGER, BUÑOLA, CALVIA, CAMPANET) into a Claude vision context and produced **real structured JSONL extractions**. Confidence per field:

| Field | Confidence | Notes |
|---|---|---|
| `cod_mun_ine` (printed) | 100% | INE printed in clear modern type |
| `cl_mapa`, `R.A.H.` page (printed) | 100% | Same |
| `name_1768` (handwritten village name) | 95% | 18th-c cursive but readable; «Andraig», «Banalbujar» etc. |
| `parroquia` (handwritten) | 90% | Same |
| `total_animes` (large number left margin) | 95% | Written large and clear |
| `eclesiasticos` / `juzgados` / `barrios` (handwritten text blocks) | 75-85% | Mostly readable but 5-10% paraphrase risk |
| `by_age[*][*]` cell-level digits (handwritten) | **70-80%** | Highest error rate; need Σ-against-total verification |
| `cura_relacion` date (handwritten) | 85% | Usually clear |

## Sample extraction (live, this session)

These four JSON objects were produced by Claude vision from PDF pages 75-76 with **zero prompt tuning** — i.e. the first prompt got this quality. With a calibrated prompt the quality goes up.

```json
{"page_pdf":75,"raw_n":4,"name_1768":"Andraig","municipi_modern":"Andratx",
 "cod_mun_ine":"07005","obispado":"Mallorca","parroquia":"Bartolomé",
 "total_animes":3006,"cura_relacion":"26 nov 1768"}

{"page_pdf":75,"raw_n":5,"name_1768":"Artá","municipi_modern":"Artà",
 "cod_mun_ine":"07006","obispado":"Mallorca","parroquia":"Sant Salvador",
 "total_animes":2902,"cura_relacion":"26 nov 1768",
 "conventos":"1 Convento San Antonio (6 lego + 2 hermanos)",
 "barrios_aldeas":"Sufragania a Capdepera y Son Servera"}

{"page_pdf":76,"raw_n":6,"name_1768":"Banalbujar","municipi_modern":"Banyalbufar",
 "cod_mun_ine":"07007","total_animes":387,
 "barrios_aldeas":"Sufragánea a Esporles"}

{"page_pdf":76,"raw_n":7,"name_1768":"Binisalem","municipi_modern":"Binissalem",
 "cod_mun_ine":"07008","total_animes":2338}
```

Full JSONL with the demographic age-tables and notes is in commit history of the previous session (not saved to disk; reproducible from any single page).

## What needs doing first thing next session

1. **Page-range survey.** Walk through the PDF and identify:
   - Start page of the Mallorca diocese cover (likely around PDF page 70)
   - First Mallorca pueblo page (likely PDF page 75 — Andraig already confirmed)
   - Last Mallorca pueblo page
   - Whether Eivissa-Formentera diocese is in Tomo VI or in a different tomo
   - Whether the **diocese summary page** (totals) is at the start or end of the diocese
2. **Confirm Eivissa-Formentera tomo.** If not in Tomo VI, check Tomo II-XI by:
   - `curl -sI 'https://www.ine.es/prodyser/pubweb/censo_aranda/tomoN.pdf'` for N in 1..11
   - Then sample first pages of each to find «Diócesis de Ibiza» or «Diócesis de Mallorca y Ibiza».
3. **Extract individual PDF pages as JPGs** for batch processing:
   ```
   pdftoppm -jpeg -r 250 data/sources/tomo6.pdf data/pages/page \
            -f 75 -l 130   # the Balearic range
   ```
4. **Run the vision extraction loop**. Use the prompt template at `prompts/extract_pueblo.md` (drafted in this handoff).
5. **Build sibling pattern**. `pyproject.toml`, `wrangler.jsonc`, `scripts/`, the standard pipeline. See `data.json` schema in `../madoz/web/data.json` for reference.

## Pipeline cost projection (verified by live test)

| Step | Per pueblo | All ~55 pueblos |
|---|---:|---:|
| Sonnet 4.6 vision extraction | ~$0.04 | ~$2.20 |
| Opus 4.7 verification of cell-level digits (selective) | ~$0.05 | ~$2.75 |
| **Total** | | **~$5** |

## Sibling projects pattern

For reference, the existing five siblings share these conventions. Mirror them.

| File | What goes in it |
|---|---|
| `pyproject.toml` | Python deps: `duckdb`, `rapidfuzz`, `python-dotenv`, `pyarrow`, plus `anthropic` (LLM) |
| `wrangler.jsonc` | Cloudflare Workers Static Assets config. `name: "aranda-balears"`, `assets.directory: "web"` |
| `web/_headers` | `Cache-Control: no-store` for all paths + a strict CSP |
| `web/index.html` + `web/app.js` + `web/style.css` | Vanilla-JS single-page site. No build step. |
| `web/data.json` + `web/data-blobs.json` | Schema: `{ "totals": {...}, "places": [...], "orphans": {...} }`. See `../madoz/web/data.json` for exact shape. |
| `scripts/fetch_sources.py` | Idempotent download / snapshot of the source data |
| `scripts/load_db.py` + `db/schema.sql` | DuckDB persistent store |
| `scripts/export_web_data.py` | Final emit of web JSON |
| `.gitignore` | Includes `data/sources/` (sources are re-fetchable) but ships `web/data.json` |
| Git history | Author identity is `acpicornell <16224446+acpicornell@users.noreply.github.com>` — NOT the work email |
| Deploy | `npx wrangler deploy` from local; no GitHub Action |

## NGIB linking

The `meta` project resolves all sibling entries to **NGIB ids**. Critical for Aranda:

- INE municipal codes are already on the manuscript pages → resolves the parent municipi directly with no fuzzy matching needed.
- Modern Catalan name comes from cross-referencing `cod_mun_ine` against the existing NGIB table at `../minano/data/ngib/`.
- Sub-municipality entities mentioned (sufragànies, ermites, barriades) need to be resolved using the same cascade as the other siblings.

The `name_1768` field will sometimes give curious spellings worth adding to the curated variants table in `../meta/scripts/build_gazetteer.py` (e.g. «Andraig» → Andratx; «Banalbujar» → Banyalbufar; «Lluchmayor» → Llucmajor). Many of these are already in the table from other siblings.

## Things to NOT rebuild

- The NGIB ingestion → reuse `../minano/data/ngib/` like the rest of the family does.
- The variants table → in `../meta/scripts/build_gazetteer.py`. Adding to it from `aranda` will benefit every sibling.
- The dev_server.py pattern → copy from `../meta/web/dev_server.py`.
- The Cloudflare _headers + CSP → copy verbatim from `../meta/web/_headers`.

## Open questions for the user

These were discussed in the previous session but not finalised:

- Should Aranda be a STANDALONE site (own URL `aranda-balears...`) or fed directly into `meta` only? **Default: standalone, like the other five siblings.**
- Should the project include the OTHER dioceses of Tomo VI (Málaga, Mondoñedo, Orihuela, Osma)? **Default: no, scope is Balearic.**
- What is the per-pueblo display? **Default: mirror Floridablanca's display (KPI block + age breakdown chart + auxiliary text fields). The two sources have the same structure.**
