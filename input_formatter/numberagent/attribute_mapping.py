"""
numberagent - attribute_mapping.py
Maps differently-named columns across datasets to one standard schema
(e.g. "owner_name", "landholder", "plot_owner" all mean the same thing).
Based on the pattern from geospatial-etl.com/automated-vector-raster-cleaning-workflows/attribute-mapping-schema-harmonization/
"""

from rapidfuzz import process
import geopandas as gpd

# canonical schema this project standardizes everything to
CANONICAL_COLUMNS = ["owner_name", "parcel_id", "land_use", "area_sqm"]


def map_columns_to_canonical(gdf: gpd.GeoDataFrame, threshold: int = 70) -> dict:
    """
    For each canonical column name, find the best-matching column
    in the input GeoDataFrame using fuzzy string matching.
    Returns a mapping dict: {canonical_name: matched_column_or_None}
    """
    input_columns = list(gdf.columns)
    mapping = {}

    for canonical in CANONICAL_COLUMNS:
        match = process.extractOne(canonical, input_columns)
        if match and match[1] >= threshold:
            mapping[canonical] = match[0]
        else:
            mapping[canonical] = None

    return mapping


def apply_column_mapping(gdf: gpd.GeoDataFrame, mapping: dict) -> gpd.GeoDataFrame:
    """Rename matched columns to their canonical names."""
    gdf = gdf.copy()
    rename_dict = {v: k for k, v in mapping.items() if v is not None}
    gdf = gdf.rename(columns=rename_dict)
    return gdf
