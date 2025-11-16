from dataclasses import dataclass, asdict
from agents.tool import function_tool as tool
import math

# =====================================================================
# Server configuration (MCP startup parameters)
# =====================================================================

@dataclass
class ServerParams:
    """
    MCP server startup parameters.

    Input
    -----
    command
        Command used to run the server
    args
        Arguments passed to the command
    env
        Environment variables

    Returns
    -------
    Dictionary form of parameters

    Behavior
    --------
    Used by MCP clients when loading the server as an external tool source.
    """
    command: str
    args: list
    env: dict

    def to_dict(self):
        # Convert dataclass to a plain dictionary for easy serialization
        return asdict(self)


# Expose a module-level default ServerParams for MCP discovery or docs
DEFAULT_SERVER_PARAMS = ServerParams(
    command="python",                           # default launcher
    args=["-m", "geolocation_server.server"],   # module path for -m
    env={},                                     # no special env required
)


# =====================================================================
# Geolocation Server
# =====================================================================

class GeolocationServer:
    """
    Geolocation Server.

    Behavior
    --------
    Provides tools for:
      - geocoding (name -> lat/lon),
      - reverse geocoding (lat/lon -> nearest known place),
      - nearby search (POIs within a radius by type).
    Dataset is synthetic but geographically plausible for Lebanon.
    """

    # =================================================================
    # Synthetic gazetteer + POI database (Lebanon-centric)
    # =================================================================
    # NOTE: coordinates are approximate and simplified for assignment use.
    PLACES = {
        # Keys are user-friendly names. Values carry lat/lon + metadata
        "AUB": {"lat": 33.901, "lon": 35.480, "city": "Beirut", "type": "university"},
        "Beirut": {"lat": 33.8938, "lon": 35.5018, "city": "Beirut", "type": "city"},
        "Baalbek": {"lat": 34.006, "lon": 36.203, "city": "Baalbek", "type": "city"},
        "Byblos": {"lat": 34.123, "lon": 35.651, "city": "Byblos", "type": "city"},
        "Sidon": {"lat": 33.560, "lon": 35.375, "city": "Sidon", "type": "city"},
        "Tyre": {"lat": 33.270, "lon": 35.196, "city": "Tyre", "type": "city"},
        "Zahle": {"lat": 33.850, "lon": 35.900, "city": "Zahle", "type": "city"},
        "Airport": {"lat": 33.8209, "lon": 35.4884, "city": "Beirut", "type": "airport"},
        "RHUH": {"lat": 33.871, "lon": 35.513, "city": "Beirut", "type": "hospital"},  # Rafik Hariri Univ. Hospital (approx)
    }

    # Small POI list for nearby search (expanded; Lebanon-centric, approximate coords)
    # NOTE
    # ----
    # - Keep 'type' values consistent with nearby_search() filtering (e.g., 'hospital', 'mall', 'venue', 'university',
    #   'museum', 'park', 'airport', 'embassy', 'pharmacy', 'restaurant', 'hotel', 'stadium', 'theater', 'beach').
    # - Coordinates are approximate and simplified for assignment/demo use.
    POIS = [
        # --- Hospitals ---
        {"name": "AUBMC", "lat": 33.896, "lon": 35.478, "type": "hospital"},
        {"name": "Rafik Hariri Univ. Hospital (RHUH)", "lat": 33.871, "lon": 35.513, "type": "hospital"},
        {"name": "Hotel-Dieu de France", "lat": 33.8869, "lon": 35.5233, "type": "hospital"},
        {"name": "LAU Medical Center – Rizk Hospital", "lat": 33.8927, "lon": 35.5159, "type": "hospital"},
        {"name": "Baalbek Governmental Hospital", "lat": 34.010, "lon": 36.210, "type": "hospital"},
        {"name": "Zahle Governmental Hospital", "lat": 33.846, "lon": 35.904, "type": "hospital"},

        # --- Universities / Schools ---
        {"name": "American University of Beirut (AUB)", "lat": 33.901, "lon": 35.480, "type": "university"},
        {"name": "Lebanese American University (LAU) Beirut", "lat": 33.8957, "lon": 35.4865, "type": "university"},
        {"name": "Saint Joseph University (USJ) – Huvelin", "lat": 33.8934, "lon": 35.5103, "type": "university"},

        # --- Malls / Shopping ---
        {"name": "Beirut Souks", "lat": 33.901, "lon": 35.504, "type": "mall"},
        {"name": "ABC Achrafieh", "lat": 33.886, "lon": 35.521, "type": "mall"},
        {"name": "ABC Verdun", "lat": 33.883, "lon": 35.486, "type": "mall"},
        {"name": "City Centre Beirut", "lat": 33.868, "lon": 35.535, "type": "mall"},

        # --- Museums / Culture ---
        {"name": "National Museum of Beirut", "lat": 33.8833, "lon": 35.5192, "type": "museum"},
        {"name": "Sursock Museum", "lat": 33.8920, "lon": 35.5171, "type": "museum"},
        {"name": "Byblos Archaeological Site", "lat": 34.1239, "lon": 35.6518, "type": "museum"},
        {"name": "Baalbek Roman Temples", "lat": 34.0060, "lon": 36.2030, "type": "museum"},

        # --- Landmarks / Venues / Theaters ---
        {"name": "Forum de Beyrouth", "lat": 33.898, "lon": 35.535, "type": "venue"},
        {"name": "Beiteddine Palace (Chouf)", "lat": 33.694, "lon": 35.579, "type": "museum"},
        {"name": "Roman Hippodrome of Tyre", "lat": 33.263, "lon": 35.205, "type": "museum"},
        {"name": "Byblos Old Souk", "lat": 34.121, "lon": 35.648, "type": "venue"},
        {"name": "Al Madina Theatre", "lat": 33.8937, "lon": 35.4867, "type": "theater"},

        # --- Parks / Beaches ---
        {"name": "Horsh Beirut", "lat": 33.8727, "lon": 35.5053, "type": "park"},
        {"name": "Rouche (Pigeon Rocks)", "lat": 33.8896, "lon": 35.4703, "type": "park"},
        {"name": "Tyre Beach (South)", "lat": 33.257, "lon": 35.214, "type": "beach"},
        {"name": "Ramlet el-Baida Beach", "lat": 33.8749, "lon": 35.4769, "type": "beach"},

        # --- Transport ---
        {"name": "Beirut–Rafic Hariri International Airport", "lat": 33.8209, "lon": 35.4884, "type": "airport"},
        {"name": "Charles Helou Bus Station", "lat": 33.8994, "lon": 35.5199, "type": "venue"},

        # --- Hotels / Restaurants / Cafés ---
        {"name": "Phoenicia Hotel Beirut", "lat": 33.9015, "lon": 35.4900, "type": "hotel"},
        {"name": "Le Gray (Downtown)", "lat": 33.8967, "lon": 35.5019, "type": "hotel"},
        {"name": "Tawlet Mar Mikhael", "lat": 33.8968, "lon": 35.5182, "type": "restaurant"},
        {"name": "Mayrig Gemmayze", "lat": 33.8944, "lon": 35.5148, "type": "restaurant"},
        {"name": "Zahle Wine House", "lat": 33.8465, "lon": 35.9035, "type": "restaurant"},

        # --- Pharmacies / Embassies / Other utilities ---
        {"name": "Pharmacy 24/7 Hamra", "lat": 33.8955, "lon": 35.4820, "type": "pharmacy"},
        {"name": "US Embassy (Awkar - approx)", "lat": 33.956, "lon": 35.589, "type": "embassy"},
        {"name": "French Embassy (Achrafieh - approx)", "lat": 33.888, "lon": 35.517, "type": "embassy"},

        # --- Sports / Stadiums ---
        {"name": "Camille Chamoun Sports City Stadium", "lat": 33.859, "lon": 35.494, "type": "stadium"},
    ]

    # =================================================================
    # Constructor
    # =================================================================

    def __init__(self):
        """
        Initialize server instance.

        Behavior
        --------
        No persistent state is required. Dataset is static.
        """
        pass  # nothing to initialize; all data are class-level constants

    # =================================================================
    # Internal helpers
    # =================================================================

    @staticmethod
    def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Compute spherical distance using the Haversine formula.

        Input
        -----
        lat1, lon1
            First coordinate
        lat2, lon2
            Second coordinate

        Returns
        -------
        Distance in kilometers

        Behavior
        --------
        Used to evaluate spatial proximity for reverse geocoding and nearby search.
        """
        r = 6371.0                                 # Earth radius [km]
        dlat = math.radians(lat2 - lat1)           # Δφ in radians
        dlon = math.radians(lon2 - lon1)           # Δλ in radians
        a = (math.sin(dlat / 2.0) ** 2
             + math.cos(math.radians(lat1))
             * math.cos(math.radians(lat2))
             * math.sin(dlon / 2.0) ** 2)
        return 2.0 * r * math.asin(math.sqrt(a))   # great-circle distance

    # =================================================================
    # Tools (attached as class attributes to avoid 'self' in JSON schema)
    # =================================================================

    @tool
    def geocode(query: str) -> dict:
        """
        Convert a place name to coordinates.

        Input
        -----
        query
            Place name to resolve (case-insensitive). Examples: "AUB", "Beirut", "Baalbek"

        Returns
        -------
        Dictionary containing 'lat' and 'lon' for the first matching place

        Behavior
        --------
        Performs a simple case-insensitive key or substring match against the internal gazetteer.
        If multiple places match, returns the best (first) match with basic metadata.
        """
        q = query.strip().lower()  # normalize user input
        # exact key match first (fast path)
        for name, info in GeolocationServer.PLACES.items():
            if name.lower() == q:
                return {"name": name, "lat": info["lat"], "lon": info["lon"], "meta": info}

        # fallback: substring scan in key or city field
        for name, info in GeolocationServer.PLACES.items():
            if q in name.lower() or q in info["city"].lower():
                return {"name": name, "lat": info["lat"], "lon": info["lon"], "meta": info}

        # no match
        return {"error": f"No match found for '{query}'"}

    @tool
    def reverse_geocode(lat: float, lon: float) -> dict:
        """
        Convert coordinates to the nearest known place.

        Input
        -----
        lat
            Latitude
        lon
            Longitude

        Returns
        -------
        Dictionary containing nearest_location (name, city, distance_km)

        Behavior
        --------
        Computes Haversine distance to all known places and returns the closest one.
        """
        best = None                # (name, info) for best candidate
        best_d = float("inf")      # track smallest distance
        for name, info in GeolocationServer.PLACES.items():
            d = GeolocationServer._haversine_km(lat, lon, info["lat"], info["lon"])
            if d < best_d:
                best = (name, info)
                best_d = d

        if best is None:
            # Defensive: in case PLACES is empty
            return {"error": "No places available."}

        name, info = best
        return {
            "nearest_location": {
                "name": name,
                "city": info["city"],
                "type": info["type"],
                "distance_km": round(best_d, 3),
                "lat": info["lat"],
                "lon": info["lon"],
            }
        }

    @tool
    def nearby_search(lat: float, lon: float, poi_type: str, radius_km: float = 5.0, limit: int = 10) -> dict:
        """
        Find nearby points-of-interest of a given type.

        Input
        -----
        lat
            Latitude
        lon
            Longitude
        poi_type
            POI type filter (e.g., 'hospital', 'mall', 'venue', 'airport')
        radius_km
            Search radius in kilometers
        limit
            Maximum number of returned results

        Returns
        -------
        Dictionary containing filtered POIs sorted by ascending distance

        Behavior
        --------
        Filters the in-memory POI list by type and distance to (lat, lon), then sorts by proximity.
        """
        t = poi_type.strip().lower()   # normalize type for comparison
        hits = []                      # accumulator for matching POIs

        for poi in GeolocationServer.POIS:
            if poi["type"].lower() != t:
                continue               # skip POIs of other types
            d = GeolocationServer._haversine_km(lat, lon, poi["lat"], poi["lon"])
            if d <= radius_km:
                entry = dict(poi)      # shallow copy to avoid mutation
                entry["distance_km"] = round(d, 3)
                hits.append(entry)

        # sort by distance, closest first
        hits.sort(key=lambda x: x["distance_km"])
        if limit is not None:
            hits = hits[:limit]        # cap results if a limit is provided

        return {
            "query": {"lat": lat, "lon": lon, "type": poi_type, "radius_km": radius_km},
            "results": hits,
        }
