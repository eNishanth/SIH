"""
cadastralagent - spatial_matching.py
Matches building footprints to cadastral parcels using spatial join,
and calculates a confidence score based on how much of the building
overlaps with the matched parcel.
"""

import geopandas as gpd


def match_buildings_to_parcels(buildings: gpd.GeoDataFrame, parcels: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    For each building, find which parcel it intersects with.
    Adds parcel attributes onto each building row.
    """
    matched = gpd.sjoin(buildings, parcels, how="left", predicate="intersects")
    return matched


def add_overlap_confidence(matched: gpd.GeoDataFrame, parcels: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Calculate what % of each building's area overlaps with its matched parcel.
    Higher % = higher confidence the match is correct.
    """
    matched = matched.copy()
    confidences = []

    parcel_geom_lookup = parcels.geometry

    for idx, row in matched.iterrows():
        parcel_idx = row.get("index_right")
        building_geom = row.geometry

        if parcel_idx is None or building_geom is None or building_geom.is_empty:
            confidences.append(0.0)
            continue

        try:
            parcel_geom = parcel_geom_lookup.loc[parcel_idx]
            intersection_area = building_geom.intersection(parcel_geom).area
            building_area = building_geom.area
            confidence = (intersection_area / building_area * 100) if building_area > 0 else 0.0
        except Exception:
            confidence = 0.0

        confidences.append(round(confidence, 2))

    matched["overlap_confidence"] = confidences
    return matched
