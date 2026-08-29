"""
shared/utils.py
Common helper functions used by geoagent and cadastralagent.
Saves real, full GeoJSON files (not simplified JSON) - each feature keeps
its full geometry plus added properties: sides, corners, elevation.
"""

import json
import logging
from pathlib import Path
import geopandas as gpd


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(name)s] %(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def load_geojson(path: str) -> gpd.GeoDataFrame:
    """Load a GeoJSON file into a GeoDataFrame."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    return gpd.read_file(path)


def add_shape_properties(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Add 'sides', 'corners', and 'elevation' as extra columns on the
    GeoDataFrame, without touching or simplifying the real geometry.
    These become normal properties in the final GeoJSON output.
    """
    gdf = gdf.copy()
    sides_list = []
    corners_list = []

    for geom in gdf.geometry:
        if geom is None or geom.is_empty or not hasattr(geom, "exterior"):
            sides_list.append(0)
            corners_list.append(0)
            continue

        coords = list(geom.exterior.coords)
        unique_points = coords[:-1] if len(coords) > 1 and coords[0] == coords[-1] else coords
        sides_list.append(len(unique_points))
        corners_list.append(len(unique_points))

    gdf["sides"] = sides_list
    gdf["corners"] = corners_list
    if "elevation" not in gdf.columns:
        gdf["elevation"] = None

    return gdf


def save_geojson(gdf: gpd.GeoDataFrame, path: str) -> None:
    """Save a GeoDataFrame as a real, full GeoJSON file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(path, driver="GeoJSON")


def save_json(data, path: str) -> None:
    """Save any JSON-serializable object (e.g. a repair report) to file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
