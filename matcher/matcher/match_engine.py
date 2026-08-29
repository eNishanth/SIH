"""
match_engine.py
Takes cadastral_output.json (parcels) + aerial_output.json (buildings),
matches each building to the parcel it most likely sits on, and scores
how well the two borders actually agree.

Confidence score (0.0 - 1.0):
    confidence = 0.7 * IoU  +  0.3 * (1 - min(area_error_pct, 100) / 100)

    - IoU (intersection-over-union of the two footprints) carries most of
      the weight, since it directly reflects "do these two shapes actually
      overlap the same ground".
    - Area error is a softer secondary signal (two shapes can have almost
      the same area but be offset from each other, so it's weighted less).

This is a v0 heuristic, not a geodetic-survey-grade algorithm — see
geometry.py's docstring for the clipping limitation. It's meant to catch
"these two datasets clearly disagree here, go look" rather than to be the
final word on parcel accuracy.

Usage as a library:
    from match_engine import load_records, match_all
    parcels = load_records("cadastral_output.json")
    buildings = load_records("aerial_output.json")
    matches = match_all(parcels, buildings)
"""
import json
from geometry import _outer_ring, project_ring, ring_area, iou, ring_centroid, planar_distance

LOW_CONFIDENCE = 0.5
MEDIUM_CONFIDENCE = 0.8
# Buildings whose nearest parcel centroid is farther than this get skipped
# as "no reasonable candidate" rather than force-matched to something far away.
MAX_CENTROID_DISTANCE_M = 250.0


def load_records(path):
    with open(path, "r") as f:
        return json.load(f)


def _record_ring_meters(record):
    """Return (ring_in_meters, ref_lat) for one flattened record, or (None, None)."""
    raw_ring = _outer_ring(record.get("coordinates"))
    if len(raw_ring) < 3:
        return None, None
    ref_lat = record.get("centroid_lat")
    if ref_lat is None:
        ref_lat = sum(p[1] for p in raw_ring) / len(raw_ring)
    return project_ring(raw_ring, ref_lat), ref_lat


def _confidence(iou_score, area_error_pct):
    area_term = 1 - min(area_error_pct, 100.0) / 100.0
    return round(max(0.0, min(1.0, 0.7 * iou_score + 0.3 * area_term)), 4)


def _status(confidence):
    if confidence >= MEDIUM_CONFIDENCE:
        return "HIGH"
    if confidence >= LOW_CONFIDENCE:
        return "MEDIUM"
    return "LOW"


def match_all(parcels, buildings):
    """Match every building to its best-overlapping parcel.

    Returns a list of dicts, one per building:
        building_id, parcel_id, iou, area_building_m2, area_parcel_m2,
        area_error_pct, centroid_distance_m, confidence, status
    Buildings with no usable geometry, or no parcel within
    MAX_CENTROID_DISTANCE_M, get status "UNMATCHED".
    """
    # Precompute projected parcel rings once.
    parcel_cache = []
    for parcel in parcels:
        ring_m, ref_lat = _record_ring_meters(parcel)
        if ring_m is None:
            continue
        parcel_cache.append({
            "record": parcel,
            "ring_m": ring_m,
            "centroid_m": ring_centroid(ring_m),
            "area_m2": ring_area(ring_m),
        })

    results = []
    for building in buildings:
        b_id = building.get("id", building.get("survey_no", "?"))
        ring_m, ref_lat = _record_ring_meters(building)
        if ring_m is None:
            results.append({
                "building_id": b_id, "parcel_id": None, "iou": 0.0,
                "area_building_m2": 0.0, "area_parcel_m2": 0.0,
                "area_error_pct": None, "centroid_distance_m": None,
                "confidence": 0.0, "status": "UNMATCHED",
                "reason": "building has no usable polygon",
            })
            continue

        b_area = ring_area(ring_m)
        b_centroid = ring_centroid(ring_m)

        # Candidate parcels: nearest by centroid, within a sane radius.
        candidates = sorted(
            parcel_cache,
            key=lambda p: planar_distance(b_centroid, p["centroid_m"]),
        )
        best = None
        for cand in candidates[:5]:  # only check the 5 nearest for speed
            dist = planar_distance(b_centroid, cand["centroid_m"])
            if dist > MAX_CENTROID_DISTANCE_M:
                break
            score = iou(ring_m, cand["ring_m"])
            if best is None or score > best["iou"]:
                best = {"cand": cand, "iou": score, "dist": dist}

        if best is None:
            results.append({
                "building_id": b_id, "parcel_id": None, "iou": 0.0,
                "area_building_m2": round(b_area, 2), "area_parcel_m2": 0.0,
                "area_error_pct": None, "centroid_distance_m": None,
                "confidence": 0.0, "status": "UNMATCHED",
                "reason": f"no parcel within {MAX_CENTROID_DISTANCE_M:.0f} m",
            })
            continue

        parcel_rec = best["cand"]["record"]
        p_area = best["cand"]["area_m2"]
        area_error_pct = (
            round(abs(b_area - p_area) / p_area * 100, 2) if p_area > 0 else 100.0
        )
        confidence = _confidence(best["iou"], area_error_pct)
        results.append({
            "building_id": b_id,
            "parcel_id": parcel_rec.get("id", parcel_rec.get("survey_no", "?")),
            "iou": round(best["iou"], 4),
            "area_building_m2": round(b_area, 2),
            "area_parcel_m2": round(p_area, 2),
            "area_error_pct": area_error_pct,
            "centroid_distance_m": round(best["dist"], 2),
            "confidence": confidence,
            "status": _status(confidence),
        })
    return results
