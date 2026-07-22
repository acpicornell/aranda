# IBESTAT cross-check data — provenance

These spreadsheets are an **independent tabulation of the 1768 Aranda census for
Mallorca**, published by IBESTAT (Institut d'Estadística de les Illes Balears).
They are used here only to **cross-check** the numeric tables of our own edition
(`web/data.json`), not as its primary source. See `scripts/ibestat_crosscheck.py`.

## Where they come from

IBESTAT's historical-census PC-Axis (JAXI) portal:

- Portal: `https://intranet.caib.es/ibestat-jaxi/`
- Navigation: **Demografia → Censos de població → Censos històrics → Segle XVIII → Cens d'Aranda (1768)**
- Node ids (JAXI `menu.do?levelId=…`):
  | Level | id |
  |---|---|
  | Censos de població | `391a8546-3995-41c0-8790-f03604bf51d6` |
  | Censos històrics | `97524e3c-205b-4c86-b4f5-7bf9774651f9` |
  | Segle XVIII | `b20c3bdd-0374-43ad-8e6b-02b2f20fb15b` |
  | Cens d'Aranda (1768) | `a5648b3a-98f5-4fe2-a7b0-7031ff26794a` |

## The two tables

| File | Table | px id |
|---|---|---|
| `I101001_7601_ca.xls` | **01. Parroquians per estat civil, sexe i grup d'edat. Mallorca** — per-parish population by marital status × sex × age group. This is the one that maps onto `web/data.json`. | `0c2d76a0-59e9-4c0d-a3a7-fe625940ad4f` |
| `I101001_7602_ca.xls` | **02. Dades del cens segons el resum publicat en el cens de Floridablanca (1787)** — the official diocese RESUMEN (126,588 souls) plus exempts and clergy. | `57630aa2-a26d-4e81-b5f1-fb874d3fcbb6` |

Download URL pattern (from the JAXI table view, after opening the table so a
session cookie exists):

```
https://intranet.caib.es/ibestat-jaxi/tabla.do?typeDownload={FMT}&lang=ca&px={PX_ID}
# FMT: 0 = PC-Axis (.px), 3 = CSV, 6 = JSON-stat, 7 = JSON
```

Programmatic download of these returned HTTP 500 for us; the files here were
saved from the browser (Excel/`.xls` export) on **2026-07-22**. The `.xls`
internal metadata shows they were produced by IBESTAT in 2012 (sheet
`I101101001_7601`).

## Important: this is NOT an independent source

Per IBESTAT's own methodology note, these tables were built by **transcribing the
same INE 2013 facsimile** of the Real Academia de la Historia's 1773 manuscript
copy that our edition extracts from. So IBESTAT is a **second, independent
transcription of the same document**, not a different source. That still makes it
a genuinely useful check — two independent readings that agree give confidence,
and where they disagree the discrepancy pinpoints a cell to re-read against the
facsimile image — but it does **not** provide higher-fidelity data, and it
carries **none of the manuscript's free-text notes** (clergy, courts, hospitals,
sufragànies), only the numbers.

## Licence

Underlying 1768 census: public domain. IBESTAT tabulation: open public-sector
statistical data; attribute IBESTAT (Institut d'Estadística de les Illes Balears)
if reused. Committed here (small, public) so the cross-check is reproducible on
any machine without re-downloading.
