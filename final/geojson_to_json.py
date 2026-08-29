"""
geojson_to_json.py
Converts any GeoJSON FeatureCollection into a plain flat JSON array -
give it a .geojson file, get a .json file back.

Each GeoJSON Feature:
    {
      "type": "Feature",
      "properties": {...},
      "geometry": {"type": "Polygon", "coordinates": [...]}
    }

becomes one flat JSON record:
    {
      ...all "properties" keys...,
      "geometry_type": "Polygon",
      "coordinates": [...],
      "centroid_lat": 12.9705,
      "centroid_lon": 77.5905
    }

Usage:
    python geojson_to_json.py <input.geojson> <output.json>

Example:
    python geojson_to_json.py data/processed/cadastral_output.geojson cadastral.json
    python geojson_to_json.py data/processed/aerial_output.geojson aerial.json
"""

import sys
import json
from pathlib import Path


def _centroid(geometry: dict):
    """Cheap centroid (average of ring vertices) - no shapely dependency needed."""
    gtype = geometry.get("type")
    coords = geometry.get("coordinates")

    def flatten_points(c):
        if not c:
            return []
        if isinstance(c[0], (int, float)):
            return [c]
        pts = []
        for sub in c:
            pts.extend(flatten_points(sub))
        return pts

    points = flatten_points(coords) if gtype else []
    if not points:
        return None, None

    lon = sum(p[0] for p in points) / len(points)
    lat = sum(p[1] for p in points) / len(points)
    return round(lat, 6), round(lon, 6)


def geojson_to_json(input_path: str, output_path: str) -> list:
    with open(input_path, "r") as f:
        data = json.load(f)

    if data.get("type") != "FeatureCollection":
        raise ValueError(f"{input_path} is not a GeoJSON FeatureCollection")

    records = []
    for feature in data.get("features", []):
        record = dict(feature.get("properties", {}))
        geometry = feature.get("geometry") or {}
        record["geometry_type"] = geometry.get("type")
        record["coordinates"] = geometry.get("coordinates")
        lat, lon = _centroid(geometry)
        record["centroid_lat"] = lat
        record["centroid_lon"] = lon
        records.append(record)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(records, f, indent=2)

    return records


if __name__ == "__main__":
    if len(sys.argv) == 3:
        input_path, output_path = sys.argv[1], sys.argv[2]
    else:
        print("Usage: python geojson_to_json.py <input.geojson> <output.json>")
        sys.exit(1)

    result = geojson_to_json(input_path, output_path)
    print(f"Converted {len(result)} feature(s) -> {output_path}")
