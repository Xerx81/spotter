from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

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
        route_geometry = None
        if route_data:
            route_geometry = route_data["geometry"]

        return Response({
            "start_location": start_location,
            "end_location": end_location,
            "route_geometry": route_geometry,
        })

    else:
        return Response({
            "message": "Error", "error": serializer.errors
        }, status=400)
