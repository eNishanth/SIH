"""
numberagent - confidence_score.py
Combines geometry overlap confidence (from cadastralagent) with
survey number match strength to produce one final confidence score per feature.
"""

import geopandas as gpd


def number_match_score(row) -> float:
    """
    Returns 100 if cleaned survey numbers match between the building
    and its matched parcel, 0 if they don't (or if either is missing).
    Assumes cleaned_number column exists on both building and parcel side
    after a spatial join (parcel-side column may be suffixed, e.g. cleaned_number_right).
    """
    left = row.get("cleaned_number", "")
    right = row.get("cleaned_number_right", "")

    if not left or not right:
        return 0.0
    return 100.0 if left == right else 0.0


def calculate_final_confidence(gdf: gpd.GeoDataFrame,
                                overlap_weight: float = 0.7,
                                number_weight: float = 0.3) -> gpd.GeoDataFrame:
    """
    Combines overlap_confidence (from cadastralagent) and number match score
    into one final_confidence score (0-100), using weighted average.
    """
    gdf = gdf.copy()

    overlap_scores = gdf["overlap_confidence"] if "overlap_confidence" in gdf.columns else 0.0
    number_scores = gdf.apply(number_match_score, axis=1)

    gdf["number_match_score"] = number_scores
    gdf["final_confidence"] = (
        overlap_scores * overlap_weight + number_scores * number_weight
    ).round(2)

    return gdf
