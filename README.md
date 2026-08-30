# GeoSync — AI-based Land Data Integration System

## Problem
Land data comes from many sources — drone surveys, satellite imagery, elevation maps, cadastral records, municipal layers, utility data, GPS surveys. Combining them is currently manual, slow, and error-prone.

## Goal
Build an AI-based system to automatically integrate and harmonize these datasets using real data, not test/sample data.

## Key Features
- Spatial matching (IoU-based)
- Topology error correction
- Coordinate system normalization
- Confidence scoring
- Automated data fetching from live sources

## Folder Structure

```
SIH/
├── final/
│   ├── input_formatter/       # fetches + cleans real data
│   │   ├── geoagent/            # fetches real parcels, repairs geometry
│   │   ├── cadastralagent/      # fetches real buildings, normalizes CRS
│   │   └── shared/               # live Overpass fetcher + GeoJSON utils
│   └── geojson_to_json.py     # converts GeoJSON -> flat JSON
│
├── matcher/
│   ├── geometry.py             # polygon clipping (IoU / overlap math)
│   ├── match_engine.py         # matches buildings to parcels, scores confidence
│   ├── report.py               # generates match summary + flagged report
│   └── run_matcher.py          # runs the full matching pipeline
│
├── data/
│   └── processed/
│       ├── cadastral_output.geojson   # real parcels (from geoagent)
│       ├── aerial_output.geojson      # real buildings (from cadastralagent)
│       ├── matched_output.json        # buildings matched to parcels
│       └── match_report.txt           # human-readable match summary
│
└── README.md
```

## Pipeline (run in this order)

**1. Fetch real data**
```bash
cd final/input_formatter
pip install -r requirements.txt

python3 geoagent/run_geoagent.py --max-tiles 10       # quick test
python3 cadastralagent/run_cadastralagent.py --max-tiles 10

# once confirmed working, run without --max-tiles for full Bengaluru
```
This produces `data/processed/cadastral_output.geojson` and `aerial_output.geojson` — real data pulled live from OpenStreetMap, no test/sample data.

**2. Match buildings to parcels**
```bash
cd ../../matcher
python3 run_matcher.py
```
This reads the two GeoJSON files, matches each building to its most likely parcel using IoU (intersection-over-union) scoring, and writes:
- `data/processed/matched_output.json` — every match with a confidence score
- `data/processed/match_report.txt` — summary: matched / unmatched / flagged for remeasurement

## Confidence Scoring

```
confidence = 0.7 * IoU(building, parcel) + 0.3 * (1 - area_error_pct / 100)
```

- **HIGH** (>= 0.8) — strong match
- **MEDIUM** (>= 0.5) — acceptable match
- **LOW** (< 0.5) or no parcel within 250m — flagged as `SUGGEST REMEASURE`

## Known Limitations (v0 — be upfront about these in the writeup)
- Only checks the 5 nearest parcels by centroid distance, for speed
- Doesn't currently subtract holes (e.g. courtyards) out of parcels
- 250m candidate radius is a starting guess — tune once tested on real Bengaluru data

## Data Sources
- Buildings + parcels: [OpenStreetMap via Overpass API](https://overpass-turbo.eu/) — live, real data
- Reference: [Microsoft Global ML Building Footprints](https://github.com/microsoft/GlobalMLBuildingFootprints)
- Reference: [Bhuvan (ISRO)](https://bhuvan.nrsc.gov.in/) — satellite imagery

## Languages / Tech
Python (geopandas, shapely, requests, FastAPI-ready) — no ML training involved; matching is done with real geometry math (IoU, polygon clipping), not a trained model.
