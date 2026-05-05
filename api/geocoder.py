import requests


def get_geocode(address: str) -> dict:
    """Returns {'lat': float, 'lon': float} or None"""

    nominatim_url = "https://nominatim.openstreetmap.org/search"
    headers = {"user-agent": "spotter"}
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
    }

    try:
        response = requests.get(nominatim_url, params=params, headers=headers, timeout=10)
        data = response.json()
        if data:
            display_name = data[0].get("display_name", "")
            if "United States" in display_name:
                return {
                    "lat": float(data[0]["lat"]),
                    "lon": float(data[0]["lon"]),
                }
            else:
                # It found the city, but it's in another country!
                print(f"Rejected: '{address}' resolved to: '{display_name}'")
                return None
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
            full_geometry = route["geometry"]["coordinates"]

            # Downsample: Keep every 10th point, but ALWAYS keep the very last point
            downsampled_geometry = full_geometry[::10] 
            if full_geometry[-1] not in downsampled_geometry:
                downsampled_geometry.append(full_geometry[-1])

            return {
                "distance_miles": route["distance"] / 1609.34,
                "duration_hours": route["duration"] / 3600,
                "geometry": downsampled_geometry,
            }
    except Exception as e:
        print(f"OSRM routing error: {e}")

    return None
