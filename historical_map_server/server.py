# historical_map_server/server.py

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
        return asdict(self)


# Expose a module-level default ServerParams for MCP discovery or docs
DEFAULT_SERVER_PARAMS = ServerParams(
    command="python",
    args=["-m", "historical_map_server.server"],
    env={},
)


# =====================================================================
# Historical Timeline Server
# =====================================================================

class HistoricalTimelineServer:
    """
    Historical Timeline Map Server.

    Behavior
    --------
    Provides tools for historical lookup based on coordinates, regions,
    or travel routes. Dataset is synthetic but historically inspired.
    """

    # =================================================================
    # Synthetic dataset with diverse regions and eras
    # =================================================================
    EVENTS = [
        # --- Beirut ---
        {"title": "Founding of Beirut as a Roman colony", "year": 14,
         "lat": 33.895, "lon": 35.480, "region": "Beirut",
         "description": "Beirut was declared a Roman colonia, marking its emergence as an imperial administrative center."},

        {"title": "Beirut School of Law rises to prominence", "year": 350,
         "lat": 33.896, "lon": 35.477, "region": "Beirut",
         "description": "The Beirut Law School shaped major Roman and Byzantine legal codes."},

        {"title": "Byzantine earthquake devastates Beirut", "year": 551,
         "lat": 33.895, "lon": 35.480, "region": "Beirut",
         "description": "A catastrophic earthquake destroyed parts of Roman Beirut."},

        {"title": "Crusader conquest of Beirut", "year": 1110,
         "lat": 33.901, "lon": 35.501, "region": "Beirut",
         "description": "Crusaders seized Beirut as part of expanding the Kingdom of Jerusalem."},

        {"title": "Beirut port explosion", "year": 2020,
         "lat": 33.901, "lon": 35.519, "region": "Beirut",
         "description": "A massive detonation reshaped the city's contemporary history."},

        # --- Baalbek ---
        {"title": "Temple of Jupiter constructed", "year": 60,
         "lat": 34.006, "lon": 36.203, "region": "Baalbek",
         "description": "The largest surviving Roman temple columns were erected here."},

        {"title": "Temple of Bacchus completed", "year": 150,
         "lat": 34.006, "lon": 36.203, "region": "Baalbek",
         "description": "One of the best-preserved ancient temples in the world."},

        {"title": "Umayyad citadel reinforced", "year": 685,
         "lat": 34.006, "lon": 36.203, "region": "Baalbek",
         "description": "Baalbek fortifications were expanded under early Islamic rule."},

        # --- Chouf ---
        {"title": "Ma'an dynasty rises", "year": 1120,
         "lat": 33.694, "lon": 35.580, "region": "Chouf",
         "description": "The Ma'an family consolidated political power in Mount Lebanon."},

        {"title": "Fakhreddine II reforms", "year": 1623,
         "lat": 33.695, "lon": 35.580, "region": "Chouf",
         "description": "Economic and administrative reforms linked Mount Lebanon to Mediterranean trade."},

        # --- Tripoli ---
        {"title": "Crusader County of Tripoli founded", "year": 1109,
         "lat": 34.438, "lon": 35.830, "region": "Tripoli",
         "description": "Tripoli became the last major Crusader polity in the Levant."},

        {"title": "Mamluk reconstruction of Tripoli", "year": 1300,
         "lat": 34.438, "lon": 35.830, "region": "Tripoli",
         "description": "Mamluks rebuilt Tripoli inland after ending Crusader rule."},

        # --- Sidon ---
        {"title": "Phoenician expansion from Sidon", "year": -900,
         "lat": 33.560, "lon": 35.375, "region": "Sidon",
         "description": "Sidon led major Phoenician maritime trade expansions across the Mediterranean."},

        # --- Tyre ---
        {"title": "Siege of Tyre by Alexander the Great", "year": -332,
         "lat": 33.270, "lon": 35.196, "region": "Tyre",
         "description": "Alexander captured Tyre after constructing a causeway to the island city."},

        # --- Byblos ---
        {"title": "Byblos develops alphabetic writing", "year": -1200,
         "lat": 34.123, "lon": 35.651, "region": "Byblos",
         "description": "Byblos played a key role in the evolution of the Phoenician alphabet."},

        # --- Akkar ---
        {"title": "Akkar on the frontier of Crusader Antioch", "year": 1100,
         "lat": 34.590, "lon": 36.080, "region": "Akkar",
         "description": "A contested border zone between Crusaders and regional Islamic powers."},

        # --- Bekaa ---
        {"title": "Anjar palace constructed", "year": 715,
         "lat": 33.726, "lon": 35.929, "region": "Bekaa",
         "description": "Anjar was built under the Umayyads as a planned palace city."},

        # --- Zahle ---
        {"title": "Rise of Zahle as a trade center", "year": 1700,
         "lat": 33.850, "lon": 35.900, "region": "Zahle",
         "description": "Zahle emerged as a major trade hub linking the Bekaa Valley with Beirut."},

        # --- National ---
        {"title": "Lebanese Independence", "year": 1943,
         "lat": 33.8889, "lon": 35.4944, "region": "Lebanon",
         "description": "Lebanon gained independence from the French Mandate."},

        {"title": "End of Civil War", "year": 1990,
         "lat": 33.888, "lon": 35.495, "region": "Lebanon",
         "description": "The Taif Agreement ended 15 years of civil conflict."},

        {"title": "Cedar Revolution", "year": 2005,
         "lat": 33.888, "lon": 35.495, "region": "Lebanon",
         "description": "Nationwide demonstrations reshaped Lebanon’s modern political landscape."},
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
        pass

    # =================================================================
    # Internal helpers
    # =================================================================

    @staticmethod
    def _distance_km(lat1, lon1, lat2, lon2):
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
        Used to evaluate spatial proximity.
        """
        r = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2
             + math.cos(math.radians(lat1))
             * math.cos(math.radians(lat2))
             * math.sin(dlon / 2) ** 2)
        return 2 * r * math.asin(math.sqrt(a))

    @staticmethod
    def _filter_years(events, start_year, end_year):
        """
        Filter dataset by year range.

        Input
        -----
        events
            List of event objects
        start_year
            Minimum year
        end_year
            Maximum year

        Returns
        -------
        Filtered list

        Behavior
        --------
        Excludes events outside the given year window.
        """
        out = []
        for ev in events:
            y = ev["year"]
            if start_year is not None and y < start_year:
                continue
            if end_year is not None and y > end_year:
                continue
            out.append(ev)
        return out


# =====================================================================
# Tools (top-level) — clean JSON schemas for the Agents SDK
# =====================================================================

@tool
def events_near_location(
    lat: float,
    lon: float,
    radius_km: float = 20.0,
    start_year: int | None = None,
    end_year: int | None = None,
) -> dict:
    """
    Retrieve historical events near a coordinate.

    Input
    -----
    lat
        Latitude
    lon
        Longitude
    radius_km
        Search radius in kilometers
    start_year
        Minimum year filter
    end_year
        Maximum year filter

    Returns
    -------
    Dictionary containing matched events

    Behavior
    --------
    Computes distance for each event and returns those that
    fall inside the search radius.
    """
    # Apply year filter
    events = HistoricalTimelineServer._filter_years(
        HistoricalTimelineServer.EVENTS, start_year, end_year
    )

    results = []
    for ev in events:
        d = HistoricalTimelineServer._distance_km(lat, lon, ev["lat"], ev["lon"])
        if d <= radius_km:
            entry = dict(ev)
            entry["distance_km"] = round(d, 3)
            results.append(entry)

    # Sort by nearest event
    results.sort(key=lambda x: x["distance_km"])

    return {
        "query": {"lat": lat, "lon": lon, "radius_km": radius_km},
        "events": results,
    }


@tool
def region_timeline(
    region_name: str,
    start_year: int | None = None,
    end_year: int | None = None,
    limit: int = 25,
) -> dict:
    """
    Generate a chronological timeline for a region.

    Input
    -----
    region_name
        Name of geographic region
    start_year
        Minimum year filter
    end_year
        Maximum year filter
    limit
        Max number of events

    Returns
    -------
    Dictionary containing ordered events

    Behavior
    --------
    Returns events whose region matches the query.
    """
    r = region_name.lower()

    # Match region
    matches = [
        ev for ev in HistoricalTimelineServer.EVENTS
        if r in ev["region"].lower()
    ]

    # Apply year filters
    matches = HistoricalTimelineServer._filter_years(matches, start_year, end_year)

    # Sort by chronological order
    matches.sort(key=lambda x: x["year"])

    # Apply limit
    if limit is not None:
        matches = matches[:limit]

    return {"region": region_name, "timeline": matches}


@tool
def route_history_summary(
    path: list[list[float]],
    corridor_km: float = 40.0,
) -> dict:
    """
    Generate historical summary for a route.

    Input
    -----
    path
        List of [lat, lon] coordinate pairs
    corridor_km
        Maximum offset distance

    Returns
    -------
    Dictionary containing route length, events, and summary

    Behavior
    --------
    Identifies all events near the travel corridor and
    generates a narrative summary across historical eras.
    """
    # Reject short routes
    if len(path) < 2:
        return {
            "selected_events": [],
            "summary": "Route is too short for evaluation.",
            "path_length_km": 0,
        }

    # Compute route length
    total = 0.0
    for i in range(len(path) - 1):
        lat1, lon1 = path[i]
        lat2, lon2 = path[i + 1]
        total += HistoricalTimelineServer._distance_km(lat1, lon1, lat2, lon2)

    # Find nearby events
    nearby = []
    for ev in HistoricalTimelineServer.EVENTS:
        # Compute closest point distance along the path
        closest = min(
            HistoricalTimelineServer._distance_km(lat, lon, ev["lat"], ev["lon"])
            for lat, lon in path
        )
        if closest <= corridor_km:
            entry = dict(ev)
            entry["distance_to_route_km"] = round(closest, 3)
            nearby.append(entry)

    # Sort historically
    nearby.sort(key=lambda x: x["year"])

    # Build narrative
    if nearby:
        regions = sorted({ev["region"] for ev in nearby})
        earliest = nearby[0]["year"]
        latest = nearby[-1]["year"]

        summary = (
            f"This route intersects historically significant regions including "
            f"{', '.join(regions)}. Events span from {earliest} to {latest}, "
            f"covering Phoenician, Hellenistic, Roman, Byzantine, Islamic, "
            f"Mamluk, Ottoman, and modern Lebanese periods."
        )
    else:
        summary = "No historical events fall within the specified corridor."

    return {
        "path_length_km": round(total, 3),
        "corridor_km": corridor_km,
        "selected_events": nearby,
        "summary": summary,
    }
