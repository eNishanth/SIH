"""
geoagent - geometry_repair.py
Detects invalid geometries and repairs them using make_valid().
"""

import geopandas as gpd
import shapely


def detect_invalid(gdf: gpd.GeoDataFrame):
    invalid_mask = ~shapely.is_valid(gdf.geometry.values)
    reasons = shapely.is_valid_reason(gdf.geometry.values)
    return invalid_mask, reasons


def repair_geometries(gdf: gpd.GeoDataFrame, invalid_mask, reasons):
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
    return bool(shapely.is_valid(gdf.geometry.values).all())
