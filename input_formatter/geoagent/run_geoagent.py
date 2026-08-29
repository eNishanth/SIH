"""
geoagent - run_geoagent.py
Main pipeline: load -> detect invalid -> repair -> verify -> check topology -> save

Run with:
    python run_geoagent.py <input_path> <output_geojson> <output_report>

Example:
    python run_geoagent.py ../data/raw/parcels.geojson ../data/processed/repaired_parcels.geojson ../data/processed/repair_report.json
"""

import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from geoagent.geometry_repair import detect_invalid, repair_geometries, verify_repair
from geoagent.topology_check import check_topology
from shared.utils import load_geojson, save_geojson, save_json_report, setup_logger

logger = setup_logger("geoagent")


def run(input_path: str, output_geojson: str, output_report: str) -> dict:
    logger.info(f"Loading: {input_path}")
    gdf = load_geojson(input_path)

    invalid_mask, reasons = detect_invalid(gdf)
    n_invalid = int(invalid_mask.sum())
    logger.info(f"Found {n_invalid} invalid geometries out of {len(gdf)}")

    gdf, repair_log = repair_geometries(gdf, invalid_mask, reasons)

    repaired_ok = verify_repair(gdf)
    logger.info(f"Repair verified: {repaired_ok}")

    topology_issues = check_topology(gdf)
    logger.info(f"Topology issues: {topology_issues}")

    save_geojson(gdf, output_geojson)
    logger.info(f"Saved repaired file: {output_geojson}")

    report = {
        "total_features": len(gdf),
        "invalid_found": n_invalid,
        "repair_log": repair_log,
        "repair_verified": repaired_ok,
        "topology_issues": topology_issues
    }
    save_json_report(report, output_report)
    logger.info(f"Saved report: {output_report}")

    return report


if __name__ == "__main__":
    if len(sys.argv) == 4:
        input_path, output_geojson, output_report = sys.argv[1], sys.argv[2], sys.argv[3]
    else:
        # defaults for quick local testing
        input_path = "../data/raw/parcels.geojson"
        output_geojson = "../data/processed/repaired_parcels.geojson"
        output_report = "../data/processed/repair_report.json"

    run(input_path, output_geojson, output_report)
