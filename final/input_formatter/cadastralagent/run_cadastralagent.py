"""
cadastralagent - run_cadastralagent.py
Fetches REAL building footprint data for Bengaluru from the live Overpass
API (tiled), normalizes its coordinate system to match the cadastral data,
and saves a real GeoJSON file to data/processed/aerial_output.geojson

No test data - this calls the live API.

Run with:
    python run_cadastralagent.py
    python run_cadastralagent.py --max-tiles 20   (quick test first)
"""

import sys
import os
import argparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cadastralagent.crs_normalization import normalize_crs
from shared.overpass_fetch import fetch_area_tiled, BENGALURU_BBOX
from shared.utils import add_shape_properties, save_geojson, setup_logger

logger = setup_logger("cadastralagent")

OUTPUT_GEOJSON = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", "aerial_output.geojson")
)


def run(bbox=BENGALURU_BBOX, tile_size_deg=0.02, max_tiles=None):
    south, west, north, east = bbox

    logger.info(f"Fetching REAL buildings for Bengaluru bbox {bbox} - live Overpass API call")
    buildings = fetch_area_tiled(south, west, north, east, tag="building",
                                  tile_size_deg=tile_size_deg, max_tiles=max_tiles)
    logger.info(f"Real buildings fetched: {len(buildings)}")

    buildings = normalize_crs(buildings)
    buildings = add_shape_properties(buildings)

    save_geojson(buildings, OUTPUT_GEOJSON)
    logger.info(f"Saved real GeoJSON: {OUTPUT_GEOJSON} ({len(buildings)} real buildings)")

    return buildings


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-tiles", type=int, default=None,
                         help="Limit tiles fetched, for a quick first test run")
    parser.add_argument("--tile-size", type=float, default=0.02)
    args = parser.parse_args()

    run(max_tiles=args.max_tiles, tile_size_deg=args.tile_size)
