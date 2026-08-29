"""
numberagent - number_cleaning.py
Standardizes survey/parcel number formats so the same plot isn't
treated as different IDs just because of formatting differences
(e.g. "123/A", "123-A", "123 A" should all become "123A").
"""

import re
import geopandas as gpd


def clean_number(value) -> str:
    """Standardize a single survey/parcel number string."""
    if value is None:
        return ""
    text = str(value).upper().strip()
    text = re.sub(r"[\s\-/_]+", "", text)  # remove spaces, dashes, slashes, underscores
    return text


def clean_number_column(gdf: gpd.GeoDataFrame, column_name: str) -> gpd.GeoDataFrame:
    """Apply clean_number() to a whole column and store result in a new column."""
    gdf = gdf.copy()
    if column_name in gdf.columns:
        gdf["cleaned_number"] = gdf[column_name].apply(clean_number)
    else:
        gdf["cleaned_number"] = ""
    return gdf
