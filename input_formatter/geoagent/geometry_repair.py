"""
geoagent - geometry_repair.py
Detects invalid geometries (self-intersections, broken polygons) and repairs them.
Based on the pattern from geospatial-etl.com/automated-vector-raster-cleaning-workflows/
"""

import geopandas as gpd
import shapely


def detect_invalid(gdf: gpd.GeoDataFrame):
    """Return a boolean mask of invalid geometries and the reason for each."""
    invalid_mask = ~shapely.is_valid(gdf.geometry.values)
    reasons = shapely.is_valid_reason(gdf.geometry.values)
    return invalid_mask, reasons


def repair_geometries(gdf: gpd.GeoDataFrame, invalid_mask, reasons):
    """Repair invalid geometries using make_valid(), log what was fixed and why."""
    repair_log = []

    for idx in gdf[invalid_mask].index:
        repair_log.append({
            "feature_index": int(idx),
            "reason": reasons[idx]
        })

    if invalid_mask.any():
        gdf = gdf.copy()
        gdf.loc[invalid_mask, "geometry"] = shapely.make_valid(
            gdf.geometry.values[invalid_mask]
        )

    return gdf, repair_log


def verify_repair(gdf: gpd.GeoDataFrame) -> bool:
    """Confirm all geometries are now valid."""
    return bool(shapely.is_valid(gdf.geometry.values).all())
