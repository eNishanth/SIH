# matcher/

A small, dependency-free engine that checks how well aerial-extracted
building footprints line up with cadastral parcel boundaries, and flags
the ones that look wrong enough to re-survey.

Sits next to `input_formatter/` as its own top-level stage — it reads the
outputs `input_formatter` produces, it doesn't live inside it.

```
project/
├── input_formatter/
│   ├── geoagent/
│   ├── cadastralagent/
│   └── shared/
├── matcher/                <- this module
│   ├── geometry.py          polygon math (area, overlap, distance) — no shapely
│   ├── match_engine.py      pairs each building to its best-fit parcel
│   ├── report.py            turns matches into a human-readable report
│   └── run_matcher.py       CLI entrypoint
└── data/
    └── processed/
        ├── cadastral_output.json
        ├── aerial_output.json
        └── matched_output.json   <- this module can write here too
```

## Run it

```bash
python run_matcher.py data/processed/cadastral_output.json data/processed/aerial_output.json --out-dir data/processed
```

Writes `matched_output.json` (one record per building: matched parcel,
IoU, area error %, confidence score, status) and `match_report.txt`
(plain-language summary + a call-out list of everything flagged for
remeasurement).

## How the confidence score works

For each building, the nearest few parcels (by centroid) are checked;
the best overlap wins the match. Confidence is:

```
confidence = 0.7 * IoU(building, parcel)  +  0.3 * (1 - area_error_pct/100)
```

- **IoU** (intersection over union of the two shapes) is the main signal —
  it directly measures "do these two borders actually agree".
- **Area error %** is a lighter secondary signal, since two shapes can
  have the same area but sit in the wrong place.

Status bands: `HIGH` (>=0.8), `MEDIUM` (>=0.5), `LOW` (<0.5). Anything
`LOW` or with no parcel within 250m gets flagged in the report as
"SUGGEST REMEASURE".

## Known limitations (this is a v0, not a survey-grade tool)

- Polygon intersection uses Sutherland-Hodgman clipping, which is exact
  only when the parcel polygon is convex. Most rectangular parcels are
  fine; a genuinely concave/L-shaped parcel can throw the overlap area
  off a bit.
- Only the outer ring of each polygon is used — holes (e.g. a courtyard
  cut out of a parcel) are ignored.
- Distances/areas use a flat equirectangular projection local to each
  building — fine at building/parcel scale, not for anything spanning
  kilometers.
- Matching only checks the 5 nearest parcels by centroid, for speed —
  fine for normal parcel densities, not tuned for adversarial layouts.

None of this needs shapely/geopandas — everything is plain Python, so it
drops into the existing project without adding dependencies.
