# Can you draw Greece with tavernas?

**[Read the story](https://etymo.co.uk/greek-tavernas/)**

The Greek follow-up to [Last orders? The UK drawn with its pubs](https://etymo.co.uk/uk-pubs/). It maps tavernas, kafeneia and ouzeri from OpenStreetMap, compares the map with the official ELSTAT business counts, and shows how hard it is to find this data in Greece.

## Data

| Data | Source | Used for |
|---|---|---|
| Every amenity=restaurant, cafe, bar and pub in Greece (21 October 2026) | OpenStreetMap via Overpass, © OpenStreetMap contributors (ODbL) | The dot map and the names |
| Statistical Business Register 2011–2023: legal units by four-digit activity (national) and three-digit activity by regional unit (2016–2023) | [ELSTAT](https://www.statistics.gr/en/statistics/-/publication/SBR01/-) | Counts over time, coverage check |
| Estimated population on 1 January, by regional unit | [ELSTAT](https://www.statistics.gr/en/statistics/-/publication/SPO18/-) | Per person figures |
| NUTS 3 boundaries 2021 | Eurostat GISCO via [Nuts2json](https://github.com/eurostat/Nuts2json) | Map areas |

## Pipeline

| Script | What it does |
|---|---|
| `01_elstat.py` | Reads the ELSTAT tables (handles the "x" confidential cells and the unnamed units in 2022), joins regional units to NUTS 3 areas with Attica as one area, adds population |
| `02_osm.py` | Sorts OpenStreetMap places into taverna, ouzeri/tsipouradiko, kafeneio, restaurant, café and bar from their names and tags |
| `03_analysis.py` | OpenStreetMap coverage against ELSTAT by area, the most common names (Greek and Latin spellings merged) |
| `04_build_site.py` | Writes `docs/data/*.js` and copies `page_template.html` to `docs/index.html` |

The OpenStreetMap file (`data/raw/osm/greece_overpass.geojson`) was downloaded by hand from overpass-turbo.eu with:

```
[out:json][timeout:600];
area["ISO3166-1"="GR"][admin_level=2]->.gr;
nwr["amenity"~"^(restaurant|cafe|bar|pub)$"](area.gr);
out center tags;
```

## Limits

- **OpenStreetMap has about 46% of the businesses ELSTAT counts**, from over 80% on Crete and the Ionian and Dodecanese islands to about 11% in Pella, Xanthi and Imathia. The dot map shows where places are mapped as much as where they are.
- **Taverna, kafeneio and ouzeri are sorted by name and tags.** Many kafeneia are mapped as plain cafés and are undercounted.
- **ELSTAT counts businesses (legal units), not premises.** A business with several branches counts once. Some island figures are confidential.
- **Greece and the UK are not measured the same way.** The comparison in the story is a rough one.

---

Made by [Eriola Trungu Impersimi](https://etymo.co.uk) · @ET
