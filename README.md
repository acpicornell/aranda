# Censo de Aranda 1768 — Balears

Digital edition of the Mallorca section of the **Censo del Conde de Aranda
(1768)**, Spain's first modern population census. Sister project of the
`nomenclators` family (`floridablanca`, `minano`, `madoz`, `nomenclator_1860`,
`riera`); shares the model and is consumed by `meta`.

**Status: complete.** All 54 pueblos/parishes of the diocese extracted and
verified; static site live (Inici · Pobles · Mapa · Demografia · Font).

## Source

The original 1768–69 parish returns were lost; the surviving copy is a **1773
transcription** kept at the **Real Academia de la Historia (Madrid)**. The INE
published a facsimile edition in **1999** (ed. Eduardo García España; digital
re-edition **2013**, NIPO 729-13-020-1 for Tomo VI).

**Provenance of what we publish.** The numbers rest on **two independent
witnesses** of the same census: the **INE facsimile** (the manuscript image) and
the **IBESTAT** tabulation (adopted as the gold standard; see
`data/ibestat/SOURCE.md`), cross-checked parish by parish. The rectors'
free-text prose was **discarded** — it survives only in an illegible degraded
copy that cannot be transcribed reliably — so only the verifiable layers
(figures + municipal identity) are published.

- **Tomo VI** covers the dioceses of Málaga, **Mallorca**, Mondoñedo, Orihuela
  and Osma. Each diocese = cover + RESUMEN + maps + blank template, then the
  pueblos.
- The Mallorca pueblos run **PDF pages 73–104** (two pueblos per page, a few
  single-pueblo pages). See `data/PAGE_MAP.md`.
- Each pueblo = a manuscript table: six age groups × two sexes ×
  {casados, solteros, total}; exentos (hidalguía, Real Servicio, Real Hacienda,
  Cruzada, Inquisición); eclesiásticos; conventos, hospicios, juzgados,
  estudios, administraciones de rentas, hermitas, barrios; and the date the
  cura signed the return.
- INE overlaid each page with **printed metadata** (`Cód.Mun.`, `Cl.Mapa`,
  `R.A.H.` page) — a clean modern anchor.

The source PDF (42 MB, 442 pages) lives at
`data/sources/tomo6_malaga_mallorca_mondoneo_orihuela_osma.pdf`
(canonical URL `https://www.ine.es/prodyser/pubweb/censo_aranda/tomo6.pdf`).

## Coverage — Mallorca only (54 parishes)

The census was organised **by dioceses, not islands**. The Obispado de
Mallorca held jurisdiction over the whole archipelago in 1768, yet this volume
contains **only Mallorca**. Per INE's own editorial note (facsimile **p. 65**):

- **Menorca** was under British rule (Treaty of Utrecht, 1708) and outside the
  diocese, so it correctly **does not appear**.
- **Eivissa and Formentera** (the Pitiüses) *did* belong to the Mallorca
  diocese in 1768 (the Eivissa diocese was created only in 1782) and **should
  have appeared, but are omitted** — "una auténtica omisión", not a copyists'
  error: the 54 surviving parish questionnaires match exactly the 54 parishes
  the official summary attributes to the diocese.

So the dataset is **49 municipalities / 54 parishes** (Palma is recorded as 6
parishes plus a "Resumen" aggregate row, which is excluded from totals to avoid
double-counting). The official diocese RESUMEN (facsimile p. 67) gives
**126,588 souls**; the pueblo-by-pueblo IBESTAT figures sum **122,969** (~2.9%
gap, mostly the "ERROR EN CIFRAS" pueblos).

## Pipeline (built)

```
fetch_sources      ▶ data/sources/tomo6.pdf (on disk)
extract_pages      ▶ data/pages/page-NNN.jpg          (pdftoppm, one JPG per page)
extract_vision     ▶ data/extracted/pueblo-NNN.json   (initial vision pass — a scaffold, later superseded)
refine_age_cells   ▶ second focused pass on pueblos whose cells don't reconcile
ibestat_apply      ▶ overwrites the figures with the IBESTAT gold standard (see data/ibestat/)
normalize          ▶ data/normalized/aranda.jsonl     (+ joins data/geo/ for Catalan name & lat/lon)
verify_totals      ▶ data/reports/verify_totals.txt   (Σ age cells vs total)
crosscheck         ▶ data/reports/crosscheck.txt      (internal arithmetic, self-contained)
export_web_data    ▶ web/data.json
clean_leftovers    ▶ drops the discarded prose; keeps only figures + identity
```

The initial vision pass was only a scaffold: the **published figures come from
the IBESTAT tabulation** (cross-checked against the facsimile), and the manuscript
**prose was discarded** as unreadable. No figure is invented.

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
**Font** (method & references). Strict CSP in `web/_headers` (CARTO tiles
allowed for the map).

Deploy: `npx wrangler deploy` (worker `aranda-balears`).

## License

Code: AGPL-3.0-or-later. Source data: INE 2013 facsimile, public domain (1768
manuscript copy).
