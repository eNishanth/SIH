"""
geoagent - topology_check.py
Checks for overlaps, duplicate geometries, and empty/invalid geometries
between features in a single dataset.
"""

import geopandas as gpd


def check_topology(gdf: gpd.GeoDataFrame) -> dict:
    issues = {
        "overlaps": [],
        "duplicates": [],
        "empty_or_invalid": []
    }

    # empty / invalid check
    for idx, geom in gdf.geometry.items():
        if geom is None or geom.is_empty or not geom.is_valid:
            issues["empty_or_invalid"].append(int(idx))

    # duplicate geometry check (exact match via WKB)
    seen = {}
    for idx, geom in gdf.geometry.items():
        if geom is None:
            continue
        key = geom.wkb
        if key in seen:
            issues["duplicates"].append({"first": seen[key], "duplicate": int(idx)})
        else:
            seen[key] = int(idx)

    # overlap check using spatial index (fast even for larger files)
    sindex = gdf.sindex
    checked_pairs = set()
    for idx, geom in gdf.geometry.items():
        if geom is None:
            continue
        possible = list(sindex.intersection(geom.bounds))
        for other_idx in possible:
            if other_idx == idx:
                continue
            pair = tuple(sorted((idx, other_idx)))
            if pair in checked_pairs:
                continue
            checked_pairs.add(pair)
            other_geom = gdf.geometry.iloc[other_idx]
            if other_geom is None:
                continue
            if geom.overlaps(other_geom):
                issues["overlaps"].append({"feature_a": int(idx), "feature_b": int(other_idx)})

    return issues
