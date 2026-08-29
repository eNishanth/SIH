"""
run_matcher.py
CLI entrypoint. Sits alongside input_formatter/ in the project layout,
as its own top-level folder (kept separate from input_formatter, same
spirit as data/ being separate — this is a distinct pipeline stage:
input_formatter cleans/matches raw data, this checks the match quality).

Usage:
    python run_matcher.py <cadastral.json> <aerial.json> [--out-dir DIR]

Example (matching the project's own file layout):
    python run_matcher.py \\
        data/processed/cadastral_output.json \\
        data/processed/aerial_output.json \\
        --out-dir data/processed

Writes:
    <out-dir>/matched_output.json   (matches + confidence, per-building)
    <out-dir>/match_report.txt      (human-readable summary + flags)
"""
import argparse
import sys
from pathlib import Path

from match_engine import load_records, match_all
from report import summarize, write_json_report, write_text_report


def main():
    parser = argparse.ArgumentParser(description="Match buildings to parcels and score confidence.")
    parser.add_argument("cadastral_json", help="Path to cadastral_output.json (parcels)")
    parser.add_argument("aerial_json", help="Path to aerial_output.json (buildings)")
    parser.add_argument("--out-dir", default=".", help="Directory to write matched_output.json + report")
    args = parser.parse_args()

    parcels = load_records(args.cadastral_json)
    buildings = load_records(args.aerial_json)

    if not parcels:
        sys.exit(f"No parcels found in {args.cadastral_json}")
    if not buildings:
        sys.exit(f"No buildings found in {args.aerial_json}")

    matches = match_all(parcels, buildings)
    summary = summarize(matches)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json_report(matches, out_dir / "matched_output.json")
    write_text_report(matches, summary, out_dir / "match_report.txt")

    print(f"Checked {summary['total_buildings']} buildings against {len(parcels)} parcels.")
    print(f"Matched: {summary['matched']}  |  Unmatched: {summary['unmatched']}")
    print(f"Flagged for remeasurement: {summary['flagged_for_remeasurement']}")
    print(f"-> {out_dir / 'matched_output.json'}")
    print(f"-> {out_dir / 'match_report.txt'}")


if __name__ == "__main__":
    main()
