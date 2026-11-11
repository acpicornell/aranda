# Source and coverage

What the edition is built from, and why it covers Mallorca only.

## Source

The original 1768–69 parish returns were lost; the surviving copy is a **1773
transcription** kept at the **Real Academia de la Historia (Madrid)**. The INE
published a facsimile edition in **1999** (ed. Eduardo García España; digital
re-edition **2013**, NIPO 729-13-020-1 for Tomo VI).

**Provenance of what we publish.** The numbers rest on **two independent
witnesses** of the same census: the **INE facsimile** (the manuscript image) and
the **IBESTAT** tabulation (adopted as the gold standard; see
`data/ibestat/SOURCE.md`), cross-checked parish by parish. The rectors'
free-text relations (their answers to the survey) were **discarded** — they
survive only in an illegible degraded copy that cannot be transcribed reliably —
so only the verifiable layers (figures + municipal identity) are published.

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

- **Menorca** was under British rule (British since 1708, ceded by the Treaty
  of Utrecht, 1713) and outside the
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
