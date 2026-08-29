"""
cadastralagent - crs_normalization.py
Ensures two GeoDataFrames use the same coordinate reference system (CRS)
before any spatial operation (join, overlap, distance) is run on them.
Based on the pattern from geospatial-etl.com/automated-vector-raster-cleaning-workflows/crs-normalization-across-mixed-datasets/
"""

import geopandas as gpd

TARGET_EPSG = 4326  # WGS84 - standard lat/lon, works well with Leaflet.js


def normalize_crs(gdf: gpd.GeoDataFrame, target_epsg: int = TARGET_EPSG) -> gpd.GeoDataFrame:
    """Reproject a GeoDataFrame to the target CRS. Assumes WGS84 if CRS is missing."""
    if gdf.crs is None:
        gdf = gdf.set_crs(epsg=target_epsg, allow_override=True)
    elif gdf.crs.to_epsg() != target_epsg:
        gdf = gdf.to_crs(epsg=target_epsg)
    return gdf


def assert_same_crs(gdf1: gpd.GeoDataFrame, gdf2: gpd.GeoDataFrame) -> None:
    """Raise an error if two GeoDataFrames don't share the same CRS."""
    epsg1 = gdf1.crs.to_epsg() if gdf1.crs else None
    epsg2 = gdf2.crs.to_epsg() if gdf2.crs else None
    if epsg1 != epsg2:
        raise ValueError(f"CRS mismatch: layer1={epsg1}, layer2={epsg2}")
