"""
matcher - match_engine.py
Matches building footprints (aerial_output.geojson) to cadastral parcels
(cadastral_output.geojson) and scores how well their borders actually
line up.

Uses the same geopandas/shapely stack as input_formatter/ (see
input_formatter/requirements.txt) - no new dependencies added to the
project. Both layers get reprojected to a local UTM CRS via
GeoDataFrame.estimate_utm_crs() before any area/overlap math, so results
are in real metres instead of degrees.
"""
import geopandas as gpd

LOW_CONFIDENCE = 0.5
MEDIUM_CONFIDENCE = 0.8
# Buildings whose nearest parcel centroid is farther than this are left
# UNMATCHED rather than force-matched to something far away.
MAX_CENTROID_DISTANCE_M = 250.0


def _project_metric(gdf: gpd.GeoDataFrame, target_crs=None) -> gpd.GeoDataFrame:
    """Reproject to a local UTM CRS (or a given CRS) for real-metre math."""
    if gdf.empty:
        return gdf
    crs = target_crs or gdf.estimate_utm_crs()
    return gdf.to_crs(crs)


def _confidence(iou_score: float, area_error_pct: float) -> float:
    area_term = 1 - min(area_error_pct, 100.0) / 100.0
    return round(max(0.0, min(1.0, 0.7 * iou_score + 0.3 * area_term)), 4)


def _status(confidence: float) -> str:
    if confidence >= MEDIUM_CONFIDENCE:
        return "HIGH"
    if confidence >= LOW_CONFIDENCE:
        return "MEDIUM"
    return "LOW"


def _id_column(gdf: gpd.GeoDataFrame) -> str:
    """OSM-derived layers use 'osm_id' (see shared/overpass_fetch.py);
    fall back to 'id' or the row index if neither is present."""
    if "osm_id" in gdf.columns:
        return "osm_id"
    if "id" in gdf.columns:
        return "id"
    return None


def match_buildings_to_parcels(parcels: gpd.GeoDataFrame, buildings: gpd.GeoDataFrame) -> list:
    """
    Returns a list of dicts, one per building:
        building_id, parcel_id, iou, area_building_m2, area_parcel_m2,
        area_error_pct, centroid_distance_m, confidence, status
    """
    if parcels.empty or buildings.empty:
        return []

    parcels_m = _project_metric(parcels)
    buildings_m = _project_metric(buildings, target_crs=parcels_m.crs)

    parcel_id_col = _id_column(parcels_m)
    building_id_col = _id_column(buildings_m)

    parcel_centroids = parcels_m.geometry.centroid

    results = []
    for b_idx, building in buildings_m.iterrows():
        b_id = building[building_id_col] if building_id_col else b_idx
        b_geom = building.geometry

        if b_geom is None or b_geom.is_empty:
            results.append({
                "building_id": b_id, "parcel_id": None, "iou": 0.0,
                "area_building_m2": 0.0, "area_parcel_m2": 0.0,
                "area_error_pct": None, "centroid_distance_m": None,
                "confidence": 0.0, "status": "UNMATCHED",
                "reason": "building has no usable geometry",
            })
            continue

        b_centroid = b_geom.centroid
        b_area = b_geom.area

        # Narrow to nearby candidates first (cheap), then score the
        # closest few by actual polygon overlap.
        distances = parcel_centroids.distance(b_centroid)
        nearby = distances[distances <= MAX_CENTROID_DISTANCE_M].sort_values()

        best = None
        for p_idx in nearby.index[:5]:
            p_geom = parcels_m.geometry.loc[p_idx]
            if p_geom is None or p_geom.is_empty:
                continue
            inter_area = b_geom.intersection(p_geom).area
            union_area = b_geom.union(p_geom).area
            iou_score = inter_area / union_area if union_area > 0 else 0.0
            if best is None or iou_score > best["iou"]:
                best = {"p_idx": p_idx, "iou": iou_score,
                        "dist": distances[p_idx], "p_area": p_geom.area}

        if best is None:
            results.append({
                "building_id": b_id, "parcel_id": None, "iou": 0.0,
                "area_building_m2": round(b_area, 2), "area_parcel_m2": 0.0,
                "area_error_pct": None, "centroid_distance_m": None,
                "confidence": 0.0, "status": "UNMATCHED",
                "reason": f"no parcel within {MAX_CENTROID_DISTANCE_M:.0f} m",
            })
            continue

        p_area = best["p_area"]
        area_error_pct = round(abs(b_area - p_area) / p_area * 100, 2) if p_area > 0 else 100.0
        confidence = _confidence(best["iou"], area_error_pct)
        p_id = parcels_m.loc[best["p_idx"], parcel_id_col] if parcel_id_col else best["p_idx"]

        results.append({
            "building_id": b_id,
            "parcel_id": p_id,
            "iou": round(best["iou"], 4),
            "area_building_m2": round(b_area, 2),
            "area_parcel_m2": round(p_area, 2),
            "area_error_pct": area_error_pct,
            "centroid_distance_m": round(best["dist"], 2),
            "confidence": confidence,
            "status": _status(confidence),
        })

    return results
