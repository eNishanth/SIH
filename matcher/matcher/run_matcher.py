"""
matcher - run_matcher.py
Reads the two real GeoJSON files the pipeline already produces -
data/processed/cadastral_output.geojson (parcels) and
data/processed/aerial_output.geojson (buildings) - matches each
building to its best-fit parcel, and scores how well the two borders
agree. Same input/output paths run_geoagent.py and run_cadastralagent.py
already use, so this just runs after them, no config needed.

Run with:
    python run_matcher.py
    python run_matcher.py --cadastral path/to/cadastral_output.geojson --aerial path/to/aerial_output.geojson
"""
import sys
import os
import argparse

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "input_formatter")))

from shared.utils import setup_logger, save_json, load_geojson  # noqa: E402
from match_engine import match_buildings_to_parcels  # noqa: E402
from report import summarize, write_text_report  # noqa: E402

logger = setup_logger("matcher")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "processed"))
DEFAULT_CADASTRAL = os.path.join(DATA_DIR, "cadastral_output.geojson")
DEFAULT_AERIAL = os.path.join(DATA_DIR, "aerial_output.geojson")
DEFAULT_MATCHED_OUT = os.path.join(DATA_DIR, "matched_output.json")
DEFAULT_REPORT_OUT = os.path.join(DATA_DIR, "match_report.txt")


def run(cadastral_path=DEFAULT_CADASTRAL, aerial_path=DEFAULT_AERIAL,
        matched_out=DEFAULT_MATCHED_OUT, report_out=DEFAULT_REPORT_OUT):
    logger.info(f"Loading parcels: {cadastral_path}")
    parcels = load_geojson(cadastral_path)
    logger.info(f"Loading buildings: {aerial_path}")
    buildings = load_geojson(aerial_path)

    logger.info(f"Matching {len(buildings)} buildings against {len(parcels)} parcels")
    matches = match_buildings_to_parcels(parcels, buildings)
    summary = summarize(matches)

    save_json(matches, matched_out)
    write_text_report(matches, summary, report_out)

    logger.info(f"Matched: {summary['matched']}  Unmatched: {summary['unmatched']}")
    logger.info(f"Flagged for remeasurement: {summary['flagged_for_remeasurement']}")
    logger.info(f"Saved: {matched_out}")
    logger.info(f"Saved: {report_out}")
    return matches, summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cadastral", default=DEFAULT_CADASTRAL)
    parser.add_argument("--aerial", default=DEFAULT_AERIAL)
    parser.add_argument("--matched-out", default=DEFAULT_MATCHED_OUT)
    parser.add_argument("--report-out", default=DEFAULT_REPORT_OUT)
    args = parser.parse_args()

    run(args.cadastral, args.aerial, args.matched_out, args.report_out)
