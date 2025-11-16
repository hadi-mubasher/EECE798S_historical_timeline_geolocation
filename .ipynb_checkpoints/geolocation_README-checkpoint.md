# 📘 Geolocation Server — README

## Overview
This project implements a **Geolocation Server** exposed as tools via the **OpenAI Agents SDK**. It provides three core map operations: **geocoding**, **reverse geocoding**, and **nearby POI search**. The agent (`geolocation_agent.py`) registers these tools and routes natural-language queries to the right operation. All data are in-memory synthetic entries centered on Lebanon (Beirut, Baalbek, Byblos, Sidon, Tyre, Zahle, etc.), suitable for assignment/demo use.

The server also defines **`ServerParams`** (command/args/env) following MCP conventions to document how a client could launch the server as an external tool source.

## Server Tools
### 1) `geocode(query: str) -> dict`
Convert a place name to coordinates.  
- Case-insensitive exact or substring match against an internal gazetteer (`PLACES`).  
- Returns the first match with `{name, lat, lon, meta}`.  
- Example inputs: `"AUB"`, `"Beirut"`, `"Baalbek"`.

### 2) `reverse_geocode(lat: float, lon: float) -> dict`
Convert coordinates to the nearest known place.  
- Uses the Haversine formula over `PLACES`.  
- Returns `{nearest_location: {name, city, type, distance_km, lat, lon}}`.

### 3) `nearby_search(lat: float, lon: float, poi_type: str, radius_km: float = 5.0, limit: int = 10) -> dict`
Find points-of-interest of a given type within a search radius.  
- Filters a synthetic `POIS` list by `poi_type` (e.g., `hospital`, `museum`, `park`, `mall`, `airport`, `embassy`, `pharmacy`, `restaurant`, `hotel`, `stadium`, `theater`, `beach`).  
- Computes distances via Haversine, sorts ascending by proximity, truncates to `limit`.  
- Returns `{query, results}`.

## Agent Integration
The agent in `geolocation_agent.py` registers all three tools and uses an OpenAI model (default **gpt-4o-mini**) to plan and call them. Flow: user message → tool call(s) (if needed) → formatted response.  
Gradio UI (`geolocation_gradio.py`) provides a minimal chat surface for interactive testing.

## How to Run
1. Install requirements:
```bash
pip install -r requirements.txt
```
2. Set your OpenAI key:
```bash
export OPENAI_API_KEY=sk-...
```
3. Run demo (CLI):
```bash
python geolocation_agent.py
```
4. Optional Gradio UI:
```bash
python geolocation_gradio.py
# (Add share=True to launch() if you need a public link)
```

## Example Prompts
**Geocoding:**  
- Geocode AUB.  
- What are the coordinates of Baalbek?  
- Give me the lat/lon for Beirut.

**Reverse geocoding:**  
- What city is closest to 33.90, 35.48?  
- Reverse geocode 33.84, 35.49.  
- Which known place is nearest to (34.01, 36.21)?

**Nearby search (POIs):**  
- Find hospital near 33.89, 35.48 within 2 km.  
- Show museums within 4 km of 33.88, 35.51.  
- Hotels near 33.90, 35.50 (limit 5).

**Edge cases:**  
- Geocode “Unknownville”.  
- Reverse geocode 0, 0.  
- Search for type “volcano” near Beirut.  

## Design Notes
- All data are local and stateless; **no external APIs**.  
- Tools include MelRok-style docstrings and concise inline comments; schemas are function-level (no `self` in JSON).  
- **`ServerParams`** are defined in `server.py` (`DEFAULT_SERVER_PARAMS`) for MCP documentation and potential external loading.  
- Distances use **Haversine** (Earth radius = 6371 km).  
- POI `type` values must match exactly for filtering; expand `POIS` as needed for richer demos.
