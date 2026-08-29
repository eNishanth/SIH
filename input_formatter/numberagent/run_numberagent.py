"""
numberagent - run_numberagent.py
Main pipeline: load matched output -> clean numbers -> map attributes -> score -> save

Run with:
    python run_numberagent.py <matched_path> <output_path> <survey_number_column>

Example:
    python run_numberagent.py ../data/processed/matched_parcels.geojson ../data/processed/final_scored_output.geojson survey_no
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from numberagent.number_cleaning import clean_number_column
from numberagent.attribute_mapping import map_columns_to_canonical, apply_column_mapping
from numberagent.confidence_score import calculate_final_confidence
from shared.utils import load_geojson, save_geojson, setup_logger

logger = setup_logger("numberagent")


def run(matched_path: str, output_path: str, survey_number_column: str = "survey_no"):
    logger.info(f"Loading matched data: {matched_path}")
    gdf = load_geojson(matched_path)

    logger.info(f"Cleaning survey number column: {survey_number_column}")
    gdf = clean_number_column(gdf, survey_number_column)

    logger.info("Mapping attribute columns to canonical schema")
    mapping = map_columns_to_canonical(gdf)
    logger.info(f"Column mapping found: {mapping}")
    gdf = apply_column_mapping(gdf, mapping)

    logger.info("Calculating final confidence scores")
    gdf = calculate_final_confidence(gdf)

    save_geojson(gdf, output_path)
    logger.info(f"Saved final output: {output_path}")

    avg_confidence = gdf["final_confidence"].mean() if "final_confidence" in gdf.columns else 0
    logger.info(f"Average final confidence: {round(avg_confidence, 2)}")

    return gdf


if __name__ == "__main__":
    if len(sys.argv) == 4:
        matched_path, output_path, survey_col = sys.argv[1], sys.argv[2], sys.argv[3]
    else:
        # defaults for quick local testing
        matched_path = "../data/processed/matched_parcels.geojson"
        output_path = "../data/processed/final_scored_output.geojson"
        survey_col = "survey_no"

    run(matched_path, output_path, survey_col)
