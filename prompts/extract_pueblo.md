# Aranda 1768 — per-pueblo extraction prompt

You are reading a single page from the Censo del Conde de Aranda (1768), Tomo VI, INE 2013 facsimile edition. Each page is one Balearic village ("pueblo"). The page combines:

- An **18th-century manuscript table** (cursive Spanish handwriting) recording demographics by age, sex, civil status, and exemption category.
- **INE-printed overlay** in clean modern type, applied in 2013: village number within the diocese, current Spanish municipi name in caps, `Cód.Mun.` (current INE code), `Cl.Mapa`, `R.A.H.` page reference.

The pages have **one or two pueblos stacked vertically**. Process **every pueblo on the page**, top to bottom, and return them as a JSON **array** (even if there is only one — return an array of length 1).

## CRITICAL — correctness over completeness

These figures feed a historical database; a wrong digit is worse than a missing one.

- **Never guess a digit.** If a handwritten cell is ambiguous, set it to `null` and lower the relevant confidence. Do not fill a plausible-looking number.
- The table is **self-checking**: per age group `casados + solteros` cells should be internally consistent, the age columns should sum to the printed **Total** column, and **varones + hembras = total_animes** (the big number in the left margin). Use these relationships to sanity-check your reads; if they don't reconcile, prefer `null` on the cells you're least sure of rather than forcing a fit.
- The INE-printed metadata (`name_modern`, `cod_mun_ine`, `cl_mapa`, `rah_page`) is modern clean type — read it exactly.

## What to extract — exact JSON schema

Return a JSON **array** of pueblo objects (no prose, no markdown fences). Each object:

```json
{
  "raw_n": <integer | null>,
  "name_modern": "<INE-printed name, caps, e.g. ANDRAIX>",
  "name_1768":   "<cursive village name from the manuscript header, e.g. Andraig>",
  "cod_mun_ine": "<5-digit string with leading zeros, e.g. 07005>",
  "cl_mapa":     "<5-digit string, e.g. 07039>",
  "rah_page":    <integer | null>,
  "obispado":    "<usually 'Mallorca' for Balearic pages>",
  "provincia":   <string | null>,
  "parroquia":   "<parish name, may be empty>",

  "total_animes": <integer | null>,   /* the large number in the left margin */

  "by_age": {
    "0-7":   { "sol_var": int|null, "sol_hem": int|null, "cas_var": int|null, "cas_hem": int|null },
    "7-16":  { ... },
    "16-25": { ... },
    "25-40": { ... },
    "40-50": { ... },
    "50+":   { ... }
  },
  "totals_row": { "var": int|null, "hem": int|null, "global": int|null },

  "exentos": {
    "hidalguia":   int|null,
    "real_servic": int|null,
    "real_hacien": int|null,
    "cruzada":     int|null,
    "inquisicion": int|null
  },

  "eclesiasticos":           "<verbatim or paraphrased; capture the parish staff>",
  "conventos_religiosos":    "<convents in the village, if any>",
  "hospicios_expositos":     "<welfare / hospice institutions>",
  "juzgados":                "<judicial admin>",
  "estudios":                "<schools mentioned>",
  "administraciones_rentas": "<tax / tobacco administration>",
  "hermitas":                "<hermitages>",
  "barrios_aldeas":          "<satellite settlements; mentions of sufragania to other villages>",

  "cura_relacion_date": "<ISO date or original text, e.g. '1768-11-26'>",
  "notes":              "<right-margin annotations, verbatim if visible>",

  "confidence": {
    "metadata":    "high|medium|low",
    "name_1768":   "high|medium|low",
    "total_animes":"high|medium|low",
    "by_age_cells":"high|medium|low",
    "text_blocks": "high|medium|low"
  }
}
```

## Guidance

- **The INE-printed metadata is your anchor.** It's modern, clean, and 100% reliable. Always populate `name_modern`, `cod_mun_ine`, `cl_mapa`, `rah_page` from it.
- **Don't invent numbers.** If a cell of the demographic table is ambiguous in the cursive, leave it `null` and mark `confidence.by_age_cells: "low"`. A blank cell is *not* `null`; it's `0` for the casados rows on young ages (no married 5-year-olds). Use null only when you can't tell.
- **The total row should match.** If you've read enough cells, verify that the row totals match the `Total` column at the right edge of the table. If they don't, downgrade confidence.
- **`total_animes` is the large number in the left margin** before the table starts (e.g. "3.006" for Andraig). It's the total population. It should equal the sum of the entire table's per-sex totals.
- **Spanish 18th-c. cursive conventions**: `t` often has a flat bar; `e` and `a` look similar; long final `r` curls down. The number `7` has a horizontal bar through it. Ignore tiny diacritics — they're often ink-blots.
- **Cura relacion date**: the closing line usually says "Dio la relación en N de [mes] de 1768" or similar. Convert to ISO if confident; otherwise verbatim.
- **Right-side marginalia**: these are 1768 notes added by the cura (errata, comments). Reproduce them verbatim (don't summarise).

## What not to do

- Don't translate Spanish to Catalan. Keep `name_1768` as written.
- Don't reformat numbers (leave "1.700" as `1700`, "2 8/100" as `2800` if context clear; null otherwise).
- Don't echo this prompt.
- Don't wrap the JSON in markdown fences.
- Don't return a bare object — always a JSON array, one element per pueblo on the page.
