"""
Shared helper functions used across geoagent, cadastralagent, and numberagent.
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


def save_geojson(gdf: gpd.GeoDataFrame, path: str) -> None:
    """Save a GeoDataFrame to GeoJSON, creating parent folders if needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(path, driver="GeoJSON")


def save_json_report(data: dict, path: str) -> None:
    """Save a dict as a formatted JSON report."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
