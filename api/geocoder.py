import requests


def get_geocode(address: str) -> dict:
    """Returns {'lat': float, 'lon': float, 'display_name': str} or None"""

    nominatim_url = "https://nominatim.openstreetmap.org/search"
    headers = {"user-agent": "spotter"}
    params = {
        "q": address + ", USA",
        "format": "json",
        "limit": 1,
        "countrycodes": "us",
    }

    try:
        response = requests.get(nominatim_url, params=params, headers=headers, timeout=10)
        data = response.json()
        if data:
            return {
                "lat": float(data[0]["lat"]),
                "lon": float(data[0]["lon"]),
                "display_name": data[0]["display_name"],
            }
    except Exception as e:
        print(f"Geocoding error for '{address}': {e}")

    return None


def get_osrm_route(waypoints: list) -> dict:
    """
    Get route from OSRM
    waypoints: list of (lat, lon)
    Returns: {'distance_miles': float, 'duration_hours': float, 'geometry': [...]}
    """

    if len(waypoints) < 2:
        return None

    coords = ";".join(f"{lon},{lat}" for lat, lon in waypoints)
    url = f"http://router.project-osrm.org/route/v1/driving/{coords}"
    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "false",
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        if data.get("code") == "Ok" and data.get("routes"):
            route = data["routes"][0]
            return {
                "distance_miles": route["distance"] / 1609.34,
                "duration_hours": route["duration"] / 3600,
                "geometry": route["geometry"]["coordinates"],
            }
    except Exception as e:
        print(f"OSRM routing error: {e}")

    return None
