from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .fuel_finder import calculate_fuel
from .geocoder import get_geocode, get_osrm_route

class LocationSerializer(serializers.Serializer):
    start_location = serializers.CharField()
    end_location = serializers.CharField()


@api_view(["POST"])
def index(request):
    serializer = LocationSerializer(data=request.data)

    if serializer.is_valid():
        start_location = serializer.validated_data.get("start_location", "")
        end_location = serializer.validated_data.get("end_location", "")

        # Get coordinates
        start_location = get_geocode(start_location)
        end_location = get_geocode(end_location)

        errors = []
        if not start_location:
            errors.append("Could not find start location")
        if not end_location:
            errors.append("Could not find end location")
        if errors:
            return Response({"error": " | ".join(errors)}, status=400)

        waypoints = [
            (start_location["lat"], start_location["lon"]),
            (end_location["lat"], end_location["lon"]),
        ]

        # Get route
        route_data = get_osrm_route(waypoints)
        route_geometry = []
        total_distance = 0
        duration_hours = 0
        if route_data:
            route_geometry = route_data["geometry"]
            total_distance = route_data["distance_miles"]
            duration_hours = route_data["duration_hours"]

        # Calculate fuel
        optimal_stops, total_fuel_cost = calculate_fuel(route_geometry, total_distance)

        return Response({
            "total_distance_miles": round(total_distance, 2),
            "duration_hours": round(duration_hours, 2),
            "total_fuel_cost": round(total_fuel_cost, 2),
            "fuel_stops": optimal_stops,
            "route_geometry": route_geometry,
        })

    else:
        return Response({
            "message": "Error", "error": serializer.errors
        }, status=400)
