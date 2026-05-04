import requests
import time
from django.core.management.base import BaseCommand

from api.models import FuelStop


class Command(BaseCommand):
    help = "Fills missing coordinates of cities in the database"

    def handle(self, *args, **options):
        # Filter the stops that don't have coordinates yet.
        missing_coords = FuelStop.objects.exclude(latitude__isnull=False, longitude__isnull=False)

        # Group them by city and state so we don't look up the same city multiple times.
        unique_cities = missing_coords.values("city", "state").distinct()

        self.stdout.write(f"Found {missing_coords.count()} stops across {unique_cities.count()} unique cities to geocode.")

        headers = {"user-agent": "spotter"}

        for loc in unique_cities:
            city = loc["city"]
            state = loc["state"]
            query = f"{city}, {state}"

            try:
                response = requests.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={"q": query, "format": "json", "limit": 1, "countrycodes": "us"},
                    headers=headers,
                    timeout=10,
                )
                data = response.json()

                if data:
                    lat = float(data[0]["lat"])
                    lon = float(data[0]["lon"])
                    FuelStop.objects.filter(city=city, state=state).update(latitude=lat, longitude=lon)
                    self.stdout.write(self.style.SUCCESS(f"Geocoded: {city}, {state}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Could not find: {city}, {state}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error for {city}, {state}: {e}"))

            # CRITICAL: Sleep for 1.1 seconds to not get banned by Nominatim
            time.sleep(1.1) 

        self.stdout.write(self.style.SUCCESS("Finished background geocoding!"))
