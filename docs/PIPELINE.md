# Pipeline, results and web

How the data were produced and checked, and how the static site is built and deployed.

## Pipeline (built)

```
fetch_sources      ▶ data/sources/tomo6_malaga_mallorca_mondoneo_orihuela_osma.pdf (on disk)
extract_pages      ▶ data/pages/page-NNN.jpg          (pdftoppm, one JPG per page)
extract_vision     ▶ data/extracted/pueblo-NNN.json   (initial vision pass — a scaffold, later superseded)
refine_age_cells   ▶ second focused pass on pueblos whose cells don't reconcile
ibestat_apply      ▶ overwrites the figures with the IBESTAT gold standard (see data/ibestat/)
normalize          ▶ data/normalized/aranda.jsonl     (+ joins data/geo/ for Catalan name & lat/lon)
verify_totals      ▶ data/reports/verify_totals.txt   (Σ age cells vs total)
crosscheck         ▶ data/reports/crosscheck.txt      (internal arithmetic, self-contained)
export_web_data    ▶ web/data.json
clean_leftovers    ▶ drops the discarded relations; keeps only figures + identity
```

The initial vision pass was only a scaffold: the **published figures come from
the IBESTAT tabulation** (cross-checked against the facsimile), and the rectors'
free-text relations were **discarded** as unreadable. No figure is invented.

No DuckDB: the dataset is one flat record per pueblo, so the normalized JSONL
is the single source of truth. The geo table (`data/geo/mallorca_municipis.json`,
cod_mun_ine → name + lat/lon, baked once from the public NGIB gazetteer) lives
**inside this project** — no runtime dependency on sibling projects.

Run: `uv run scripts/<name>.py`. Vision steps need `ANTHROPIC_API_KEY` (env or
local `.env`).

## Results

- All **54** pueblos have their total confirmed (*varones + hembras = ánimas*);
  **48 of 54** also reconcile the full age × sex × marital detail (Σ cells =
  margin total). The other 6 don't: 3 (Inca, Porreres, Sant Llorenç des
  Cardassar) carry the INE **«ERROR EN CIFRAS»** stamp and the rest are
  arithmetic noise — the 1768 manuscript itself doesn't add up there; we keep the
  cura's figures as written.
- Mallorca population 1768 (IBESTAT figures): **122,969** (V 59,702 · H 63,267).

## Web

Static, no build step: `web/index.html` + `web/app.js` + `web/style.css`,
Leaflet vendored under `web/vendor/`. Tabs: **Inici** (history of the census &
the count of Aranda, the Menorca/Eivissa note, cross-check), **Pobles**
(searchable table + per-pueblo detail), **Mapa** (Leaflet, one marker per
pueblo), **Demografia** (pyramid, sex ratio, marital structure, indicators),
**Font** (method & references). Strict CSP in `web/_headers` (OpenStreetMap tiles
allowed for the map).

Deploy: `npx wrangler deploy` (worker `aranda-balears`).
