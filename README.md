# 📘 Map Servers — README (Historical Timeline + Geolocation)

## Overview
This repository contains **two small map servers** implemented as tools for the **OpenAI Agents SDK**:

1) **Historical Timeline Server** — retrieve structured history by **location**, **region**, or **route corridor**.  
2) **Geolocation Server** — perform **geocoding**, **reverse geocoding**, and **nearby POI search** over a synthetic Lebanon‑centric dataset.

Each server ships with a minimal **Agent** and optional **Gradio UI** for interactive testing.

---

## 🔷 Historical Timeline Server

### Server Tools
1. **`events_near_location(lat, lon, radius_km=20, start_year=None, end_year=None)`**  
   Find historical events around a coordinate using the Haversine formula. Optional year filtering; results sorted by distance.

2. **`region_timeline(region_name, start_year=None, end_year=None, limit=25)`**  
   Build a chronological timeline for a region. Case‑insensitive matching, year window, chronological sort, and truncation by `limit`.

3. **`route_history_summary(path, corridor_km=40)`**  
   Generate a narrative for a polyline (list of waypoints). Computes total path length, collects events within a corridor, and summarizes ancient → medieval → modern transitions.

### Agent Integration
The agent in `historical_map_agent.py` registers the three tools and uses an OpenAI model (default **gpt-4o-mini**) to plan and call them:

```
user message → (optional) tool call(s) → final formatted response
```

### How to Run 
```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...

# CLI demo
python historical_map_agent.py

# Optional Gradio UI
python historical_map_gradio.py
```

### Example Prompts
**Localized**  
- Show historical events within 5 km of Beirut.  
- Find events near Tripoli around the year 1100.  
- Show latest historical events of Beirut Port.

**Region timelines**  
- Give me a full historical timeline for Chouf.  
- Show the timeline for Sidon from -1000 to -200.  
- What are the earliest recorded events in Byblos?

**Route‑based**  
- I am traveling from Beirut to Zahle. Summarize the major historical periods along this route.  
- Generate a route history summary for the path [Beirut → Jounieh → Byblos].

**Edge cases**  
- Show events near 0, 0.  
- Give me historical events in Baalbek from 5000 to 7000.  
- Summarize the history along my route.

### Design Notes
- All data are local and stateless; **no external APIs**.  
- Distance uses **Haversine** (Earth radius = 6371 km).

---

## 🔷 Geolocation Server

### Server Tools
1. **`geocode(query: str) -> dict`**  
   Convert a place name to coordinates. Case‑insensitive exact/substring match over an in‑memory gazetteer (`PLACES`). Returns `{name, lat, lon, meta}`.

2. **`reverse_geocode(lat: float, lon: float) -> dict`**  
   Convert coordinates to the nearest known place (Haversine over `PLACES`). Returns `{nearest_location: {name, city, type, distance_km, lat, lon}}`.

3. **`nearby_search(lat: float, lon: float, poi_type: str, radius_km: float = 5.0, limit: int = 10) -> dict`**  
   Filter synthetic `POIS` by `poi_type` (e.g., `hospital`, `museum`, `park`, `mall`, `airport`, `embassy`, `pharmacy`, `restaurant`, `hotel`, `stadium`, `theater`, `beach`), compute distances, sort ascending by proximity, and truncate to `limit`.

### Agent Integration
The agent in `geolocation_agent.py` registers the three tools and uses **gpt-4o-mini** by default.  
The **Gradio UI** (`geolocation_gradio.py`) provides a minimal chat app for interactive testing.

### How to Run
```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...

# CLI demo
python geolocation_agent.py

# Optional Gradio UI
python geolocation_gradio.py
# (Add share=True to launch() if you need a public link)
```

### Example Prompts
**Geocoding**  
- Geocode AUB.  
- What are the coordinates of Baalbek?  
- Give me the lat/lon for Beirut.

**Reverse geocoding**  
- What city is closest to 33.90, 35.48?  
- Reverse geocode 33.84, 35.49.  
- Which known place is nearest to (34.01, 36.21)?

**Nearby search (POIs)**  
- Find hospital near 33.89, 35.48 within 2 km.  
- Show museums within 4 km of 33.88, 35.51.  
- Hotels near 33.90, 35.50 (limit 5).

**Edge cases**  
- Geocode “Unknownville”.  
- Reverse geocode 0, 0.  
- Search for type “volcano” near Beirut.

### Design Notes
- Local, deterministic, Lebanon‑centric dataset; **no external APIs**.  
- Function‑level tools (no `self` in tool schemas).  
- Distances computed with **Haversine**.

---

## 🧩 MCP / ServerParams
Each server defines **`ServerParams`** (command/args/env) per MCP conventions to document how a client could launch it as an external tool source. A module‑level `DEFAULT_SERVER_PARAMS` is provided in each `server.py` for discovery or documentation.

---

## 🧪 Testing & Interactive Demos
- **Historical**: `historical_map_agent.py` (CLI), `historical_map_gradio.py` (Gradio)  
- **Geolocation**: `geolocation_agent.py` (CLI), `geolocation_gradio.py` (Gradio)  



---

## Notes
- Default model: **gpt-4o-mini** (configurable).  
- Be sure to set `OPENAI_API_KEY` before running agents or UIs.  
- All datasets are **synthetic** and simplified for assignment purposes.
