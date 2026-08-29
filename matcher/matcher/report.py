"""
report.py
Turns match_engine's output into:
  1. matched_output.json — the raw match records (drop-in for
     data/processed/matched_output.json in the project layout)
  2. a plain-text report summarizing overall quality and calling out
     the specific building/parcel pairs that look wrong enough to
     warrant a re-survey.
"""
import json
from match_engine import LOW_CONFIDENCE, MEDIUM_CONFIDENCE


def summarize(matches):
    total = len(matches)
    unmatched = [m for m in matches if m["status"] == "UNMATCHED"]
    matched = [m for m in matches if m["status"] != "UNMATCHED"]
    low = [m for m in matched if m["status"] == "LOW"]
    medium = [m for m in matched if m["status"] == "MEDIUM"]
    high = [m for m in matched if m["status"] == "HIGH"]
    avg_conf = round(sum(m["confidence"] for m in matched) / len(matched), 4) if matched else 0.0
    avg_area_error = (
        round(sum(m["area_error_pct"] for m in matched) / len(matched), 2)
        if matched else 0.0
    )
    return {
        "total_buildings": total,
        "matched": len(matched),
        "unmatched": len(unmatched),
        "high_confidence": len(high),
        "medium_confidence": len(medium),
        "low_confidence": len(low),
        "average_confidence": avg_conf,
        "average_area_error_pct": avg_area_error,
        "flagged_for_remeasurement": len(low) + len(unmatched),
    }


def write_json_report(matches, path):
    with open(path, "w") as f:
        json.dump(matches, f, indent=2)


def write_text_report(matches, summary, path):
    lines = []
    lines.append("BUILDING <-> PARCEL BOUNDARY MATCH REPORT")
    lines.append("=" * 42)
    lines.append(f"Total buildings checked : {summary['total_buildings']}")
    lines.append(f"Matched to a parcel     : {summary['matched']}")
    lines.append(f"Unmatched (no candidate): {summary['unmatched']}")
    lines.append(f"  High confidence (>= {MEDIUM_CONFIDENCE})  : {summary['high_confidence']}")
    lines.append(f"  Medium confidence      : {summary['medium_confidence']}")
    lines.append(f"  Low confidence (< {LOW_CONFIDENCE})    : {summary['low_confidence']}")
    lines.append(f"Average confidence      : {summary['average_confidence']}")
    lines.append(f"Average area error      : {summary['average_area_error_pct']}%")
    lines.append("")
    lines.append(f"FLAGGED FOR REMEASUREMENT: {summary['flagged_for_remeasurement']}")
    lines.append("-" * 42)

    flagged = [m for m in matches if m["status"] in ("LOW", "UNMATCHED")]
    if not flagged:
        lines.append("None. Every building matched its parcel with reasonable confidence.")
    for m in flagged:
        if m["status"] == "UNMATCHED":
            lines.append(
                f"  [UNMATCHED] building {m['building_id']}: {m.get('reason', 'no match found')}"
                " -> SUGGEST REMEASURE (check building footprint / nearby parcel data)"
            )
        else:
            lines.append(
                f"  [LOW] building {m['building_id']} vs parcel {m['parcel_id']}: "
                f"IoU={m['iou']}, area_error={m['area_error_pct']}%, "
                f"confidence={m['confidence']} -> SUGGEST REMEASURE"
            )

    lines.append("")
    lines.append("All matches:")
    lines.append("-" * 42)
    for m in matches:
        lines.append(
            f"  building {m['building_id']:>6} -> parcel {str(m['parcel_id']):>6} "
            f"| status={m['status']:<10} confidence={m['confidence']}"
        )

    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
