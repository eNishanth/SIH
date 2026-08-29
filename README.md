# GeoSync — AI-based Land Data Integration System

## Problem
Land data comes from many sources — drone surveys, satellite imagery, elevation maps, cadastral records, municipal layers, utility data, GPS surveys. Combining them is currently manual, slow, and error-prone.

## Goal
Build an AI-based system to automatically integrate and harmonize these datasets.

## Key Features
- Spatial matching
- Topology error correction
- Attribute mapping
- Coordinate conversion
- Change detection
- Conflict resolution
- Confidence scoring

## Outcome
- Less manual GIS work
- More accurate land records
- Easier data sharing between departments
- Faster cadastral finalization

## Suggested Tech
AI/ML, GeoAI, GIS, spatial databases, computer vision, cloud computing

## Folder Structure

```
geosync/
├── data/              # buildings, parcels, satellite imagery
├── matching_engine/   # spatial matching + confidence score + topology fix
├── change_detection/  # OpenCV before/after comparison
├── outputs/           # final matched map data
├── backend/           # FastAPI server, connects data to frontend
└── frontend/          # Leaflet.js map, shows results
```

## Steps

**1. data/**
Download buildings + parcels from OpenStreetMap (Overpass Turbo), imagery from Bhuvan. Save as GeoJSON.
Tools: Overpass Turbo, QGIS

**2. matching_engine/**
Python script matches buildings to parcels, scores confidence, fixes broken polygons.
Libraries: geopandas, shapely

**3. change_detection/**
Python script compares before/after images to detect changes.
Library: opencv-python

**4. outputs/**
Save results from steps 2 and 3 as GeoJSON/JSON. No coding, just storage.

**5. backend/**
FastAPI server reads `outputs/`, serves as JSON API.
Run: `uvicorn main:app --reload`

**6. frontend/**
HTML/CSS/JS + Leaflet.js map calls the API, shows results color-coded by confidence.

## Build Order
data → matching_engine → change_detection → outputs → backend → frontend

## Languages
Python (processing, matching, API) + JavaScript/HTML/CSS (map frontend)

Datasets-
https://github.com/microsoft/GlobalMLBuildingFootprints  (3D Footprint)
https://overpass-turbo.eu/  (Cadastral Data)
https://bhuvan.nrsc.gov.in/  (Areal Data)
