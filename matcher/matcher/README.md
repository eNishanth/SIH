# matcher/

Checks how well aerial-extracted building footprints line up with
cadastral parcel boundaries, and flags the ones worth re-surveying.

Sits at the **top level of the repo**, as its own stage — a sibling to
`input_formatter/` and `data/`, not nested inside `input_formatter/`:

```
SIH/
├── input_formatter/
│   ├── geoagent/
│   ├── cadastralagent/
│   ├── shared/
│   └── requirements.txt
├── matcher/                  <- add this folder here
│   ├── __init__.py
│   ├── match_engine.py        does the matching + scoring
│   ├── report.py               turns matches into a report
│   ├── run_matcher.py          entrypoint
│   └── README.md
└── data/
    └── processed/
        ├── cadastral_output.geojson   (from geoagent)
        ├── aerial_output.geojson      (from cadastralagent)
        ├── matched_output.json        <- this module writes this
        └── match_report.txt           <- and this
```

## Why it's built this way

Reuses what's already in the repo instead of adding anything new:
- Reads the real `.geojson` outputs `run_geoagent.py` /
  `run_cadastralagent.py` already produce, via `shared.utils.load_geojson`.
- Uses `geopandas` + `shapely` (already in `input_formatter/requirements.txt`)
  for real polygon intersection/union — no extra dependency added.
- Reprojects both layers to a local UTM CRS
  (`GeoDataFrame.estimate_utm_crs()`) before computing area/overlap, so
  results are in real metres, not degrees.
- Writes with `shared.utils.save_json`, same as the rest of the pipeline.
- Picks up the `osm_id` column, matching `shared/overpass_fetch.py`'s ID
  convention.

## Run it

```bash
cd matcher
python run_matcher.py
```

Defaults to `data/processed/cadastral_output.geojson` and
`aerial_output.geojson`, and writes `matched_output.json` +
`match_report.txt` back into `data/processed/`. Override paths with
`--cadastral`, `--aerial`, `--matched-out`, `--report-out` if needed.

## Confidence score

```
confidence = 0.7 * IoU(building, parcel)  +  0.3 * (1 - area_error_pct / 100)
```

- **IoU** (intersection over union) is the main signal.
- **Area error %** is a lighter secondary signal, since two shapes can
  have similar area but sit in the wrong place.

Bands: `HIGH` (>=0.8), `MEDIUM` (>=0.5), `LOW` (<0.5). `LOW` or
no-parcel-within-250m gets flagged `SUGGEST REMEASURE` in the report.

## Limitations (v0, be upfront about these in your writeup)

- Only checks the 5 nearest parcels by centroid distance, for speed.
- Doesn't currently subtract holes (e.g. courtyards) out of parcels.
- 250m candidate radius is a starting guess, not tuned on real data yet
  — tighten or loosen it once you see it run on the actual Bengaluru
  dataset.
