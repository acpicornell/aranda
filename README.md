# Censo de Aranda 1768 — Balears

[![Deploy](https://github.com/acpicornell/aranda/actions/workflows/deploy.yml/badge.svg)](https://github.com/acpicornell/aranda/actions/workflows/deploy.yml)

Digital edition of the Mallorca section of the **Censo del Conde de Aranda
(1768)**, Spain's first modern population census: the parish-by-parish figures,
verified and published as data, a map and a demographic profile.

Live at **<https://aranda.corpusbalear.org>**. Part of
[Corpus Balear](https://corpusbalear.org) and of its `nomenclators` family
(`floridablanca`, `minano`, `madoz`, `nomenclator_1860`, `riera`); shares the
model and is consumed by `meta`.

**Status: complete.** All 54 pueblos/parishes of the diocese extracted and
verified; static site live (Inici · Pobles · Mapa · Demografia · Font).

## What's in it

- **49 municipalities / 54 parishes** — Mallorca only: Menorca was outside the
  diocese, and Eivissa and Formentera are a genuine omission of the volume.
- Mallorca population 1768 (IBESTAT figures): **122,969** (V 59,702 · H 63,267),
  against **126,588 souls** in the official diocese RESUMEN.
- All **54** totals confirmed (*varones + hembras = ánimas*); **48 of 54** also
  reconcile the full age × sex × marital detail.
- Per pueblo: six age groups × two sexes × marital status, exentos,
  eclesiásticos, institutions, and the date the cura signed the return.

## How it was made

The numbers rest on two independent witnesses of the same census: the INE
facsimile (1999, digital re-edition 2013) of the 1773 copy kept at the Real
Academia de la Historia, and the IBESTAT tabulation, adopted as the gold standard
and cross-checked parish by parish. An initial vision pass over the facsimile was
only a scaffold; no figure is invented. The rectors' free-text relations survive
only in an illegible copy and were discarded.

## Run / build locally

```sh
uv run scripts/<name>.py     # each pipeline step; vision steps need ANTHROPIC_API_KEY
npx wrangler deploy          # the site in web/ has no build step (worker aranda-balears)
```

## Documentation

- [docs/SOURCE.md](docs/SOURCE.md) — the source volume, provenance of the
  figures, page layout, and why the coverage is Mallorca only.
- [docs/PIPELINE.md](docs/PIPELINE.md) — pipeline steps and outputs,
  verification results, and the static web.
- [data/PAGE_MAP.md](data/PAGE_MAP.md) — pueblo-to-page map of the facsimile.
- [data/ibestat/SOURCE.md](data/ibestat/SOURCE.md) — the IBESTAT gold standard.

## License

Code: AGPL-3.0-or-later. Source data: INE 2013 facsimile, public domain (1768
manuscript copy).
