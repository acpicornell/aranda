# Page-range survey — Tomo VI (verified 2026-06-02)

Definitive boundaries of the Balearic (Mallorca) section, confirmed by visual
survey of the JPG bursts at 150 dpi.

| PDF page | Content |
|---|---|
| 70 | Blank RAH template page ("IMPRESO usado por la Real Academia de la Historia") |
| 71–72 | Blank |
| **73** | **First Mallorca pueblo — #1 ALARO (07001)**, single pueblo (diocese opening page). Footer "MALLORCA 73". |
| 74 | #2 ALCUDIA (07003), #3 ALGAIDA (07004) |
| 75 | #4 ANDRAIX (07005), #5 ARTA (07006) |
| … | two pueblos per page (a few single-pueblo pages) |
| 95 | #39 PORRERAS (07043), #40 PUEBLA LA (07044) |
| 100 | #48 SANTA MARIA DEL CAMI (07056), #49 SANTAÑY (07057) |
| 103 | #54 VALLDEMOSA (07063), single |
| **104** | **Last Mallorca pueblo — #55 VILLAFRANCA DE BONANY (07065)**, single. Footer "MALLORCA 104". |
| 105 | Diocese cover: "Diócesis de Mondoñedo" (Galicia — next diocese begins) |
| 106 | Blank |
| 108 | Mondoñedo legend + Spain map (province codes 27xxx) |

## Conclusions (resolve HANDOFF open questions)

- **Mallorca pueblo pages: 73–104 inclusive. 55 pueblos.**
- **Eivissa-Formentera is NOT in Tomo VI.** Mallorca is immediately followed by
  Mondoñedo. Historically consistent: in 1768 Eivissa was not part of the
  Obispado de Mallorca (the Diocese of Eivissa was only created in 1782), so it
  does not appear under this diocese. Menorca excluded (British rule 1708–1782).
- The extraction range for `extract_pages.py` / `extract_vision.py` is
  **`--first 73 --last 104`**.
- Pueblo order number ("Número de Orden del Pueblo dentro del Obispado") is
  printed top-left of each pueblo; INE `Cód.Mun.` is the modern anchor (Mallorca
  province = 07xxx).
