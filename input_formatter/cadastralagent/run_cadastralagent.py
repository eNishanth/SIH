"""
cadastralagent - run_cadastralagent.py
Main pipeline: load repaired parcels + buildings -> normalize CRS -> match -> save

Run with:
    python run_cadastralagent.py <parcels_path> <buildings_path> <output_path>

Example:
    python run_cadastralagent.py ../data/processed/repaired_parcels.geojson ../data/raw/buildings.geojson ../data/processed/matched_parcels.geojson
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cadastralagent.crs_normalization import normalize_crs, assert_same_crs
from cadastralagent.spatial_matching import match_buildings_to_parcels, add_overlap_confidence
from shared.utils import load_geojson, save_geojson, setup_logger

logger = setup_logger("cadastralagent")


def run(parcels_path: str, buildings_path: str, output_path: str):
    logger.info(f"Loading parcels: {parcels_path}")
    parcels = load_geojson(parcels_path)

    logger.info(f"Loading buildings: {buildings_path}")
    buildings = load_geojson(buildings_path)

    logger.info("Normalizing CRS for both layers")
    parcels = normalize_crs(parcels)
    buildings = normalize_crs(buildings)
    assert_same_crs(parcels, buildings)

    logger.info("Matching buildings to parcels")
    matched = match_buildings_to_parcels(buildings, parcels)

    logger.info("Calculating overlap confidence")
    matched = add_overlap_confidence(matched, parcels)

    save_geojson(matched, output_path)
    logger.info(f"Saved matched output: {output_path}")

    logger.info(f"Total buildings matched: {len(matched)}")
    return matched


if __name__ == "__main__":
    if len(sys.argv) == 4:
        parcels_path, buildings_path, output_path = sys.argv[1], sys.argv[2], sys.argv[3]
    else:
        # defaults for quick local testing
        parcels_path = "../data/processed/repaired_parcels.geojson"
        buildings_path = "../data/raw/buildings.geojson"
        output_path = "../data/processed/matched_parcels.geojson"

    run(parcels_path, buildings_path, output_path)
