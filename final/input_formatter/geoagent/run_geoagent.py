"""
geoagent - run_geoagent.py
Fetches REAL parcel (landuse) data for Bengaluru from the live Overpass API
(tiled, so it doesn't time out), repairs invalid geometry, and saves a
real GeoJSON file to data/processed/cadastral_output.geojson

No test data - this calls the live API.

Run with:
    python run_geoagent.py
    python run_geoagent.py --max-tiles 20    (quick test on a smaller area first)
"""

import sys
import os
import argparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from geoagent.geometry_repair import detect_invalid, repair_geometries, verify_repair
from shared.overpass_fetch import fetch_area_tiled, BENGALURU_BBOX
from shared.utils import add_shape_properties, save_geojson, setup_logger

logger = setup_logger("geoagent")

OUTPUT_GEOJSON = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed", "cadastral_output.geojson")
)


def run(bbox=BENGALURU_BBOX, tile_size_deg=0.02, max_tiles=None):
    south, west, north, east = bbox

    logger.info(f"Fetching REAL parcels (landuse) for Bengaluru bbox {bbox} - live Overpass API call")
    gdf = fetch_area_tiled(south, west, north, east, tag="landuse",
                            tile_size_deg=tile_size_deg, max_tiles=max_tiles)
    logger.info(f"Real parcels fetched: {len(gdf)}")

    invalid_mask, reasons = detect_invalid(gdf)
    n_invalid = int(sum(invalid_mask)) if len(gdf) > 0 else 0
    logger.info(f"Found {n_invalid} invalid geometries out of {len(gdf)}")

    gdf, repair_log = repair_geometries(gdf, invalid_mask, reasons)
    repaired_ok = verify_repair(gdf) if len(gdf) > 0 else True
    logger.info(f"Repair verified: {repaired_ok}")

    gdf = add_shape_properties(gdf)

    save_geojson(gdf, OUTPUT_GEOJSON)
    logger.info(f"Saved real GeoJSON: {OUTPUT_GEOJSON} ({len(gdf)} real parcels)")

    return gdf


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-tiles", type=int, default=None,
                         help="Limit tiles fetched, for a quick first test run")
    parser.add_argument("--tile-size", type=float, default=0.02)
    args = parser.parse_args()

    run(max_tiles=args.max_tiles, tile_size_deg=args.tile_size)
