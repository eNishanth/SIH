"""
shared/overpass_fetch.py
Fetches REAL OpenStreetMap data - buildings and land parcels - from the
live Overpass API. Includes tiling so a large area (full Bengaluru) can
be fetched in small chunks without timing out the free public server.

No test data - every function here calls the real live API.
"""

import time
import requests
import geopandas as gpd
from shapely.geometry import Polygon

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Approximate bounding box covering all of Bengaluru city
# format: south, west, north, east
BENGALURU_BBOX = (12.83, 77.46, 13.14, 77.78)


def build_query(south: float, west: float, north: float, east: float, tag: str) -> str:
    return f"""
    [out:json][timeout:60];
    way["{tag}"]({south},{west},{north},{east});
    out geom;
    """


def fetch_osm_ways(south: float, west: float, north: float, east: float, tag: str) -> list:
    """Single live call to Overpass API for one bounding box."""
    query = build_query(south, west, north, east, tag)
    response = requests.post(OVERPASS_URL, data={"data": query}, timeout=90)
    response.raise_for_status()
    data = response.json()
    return data.get("elements", [])


def ways_to_geodataframe(elements: list) -> gpd.GeoDataFrame:
    """Convert Overpass 'way' elements into a GeoDataFrame of polygons, de-duplicated by osm_id."""
    records = []
    geoms = []
    seen_ids = set()

    for el in elements:
        osm_id = el.get("id")
        if osm_id in seen_ids:
            continue

        geom_points = el.get("geometry")
        if not geom_points or len(geom_points) < 3:
            continue

        coords = [(pt["lon"], pt["lat"]) for pt in geom_points]
        polygon = Polygon(coords)
        if not polygon.is_valid or polygon.is_empty:
            continue

        seen_ids.add(osm_id)
        geoms.append(polygon)
        tags = el.get("tags", {})
        record = {"osm_id": osm_id}
        record.update(tags)
        records.append(record)

    if not geoms:
        return gpd.GeoDataFrame(columns=["osm_id", "geometry"], geometry="geometry", crs="EPSG:4326")

    return gpd.GeoDataFrame(records, geometry=geoms, crs="EPSG:4326")


def make_tiles(south: float, west: float, north: float, east: float, tile_size_deg: float = 0.02):
    """Split a big bounding box into a grid of small tiles (~2km each by default)."""
    tiles = []
    lat = south
    while lat < north:
        lon = west
        next_lat = min(lat + tile_size_deg, north)
        while lon < east:
            next_lon = min(lon + tile_size_deg, east)
            tiles.append((lat, lon, next_lat, next_lon))
            lon = next_lon
        lat = next_lat
    return tiles


def fetch_area_tiled(south: float, west: float, north: float, east: float,
                      tag: str, tile_size_deg: float = 0.02,
                      pause_between_calls: float = 1.0,
                      max_tiles: int = None) -> gpd.GeoDataFrame:
    """
    Fetch real OSM data for a large area by breaking it into small tiles,
    calling the live API once per tile, and merging all results.
    Use this for city-scale areas like full Bengaluru.
    """
    tiles = make_tiles(south, west, north, east, tile_size_deg)
    if max_tiles:
        tiles = tiles[:max_tiles]

    all_elements = []
    for (s, w, n, e) in tiles:
        elements = fetch_osm_ways(s, w, n, e, tag)
        all_elements.extend(elements)
        time.sleep(pause_between_calls)  # be respectful of the free public server

    return ways_to_geodataframe(all_elements)
