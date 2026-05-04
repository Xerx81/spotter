import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction

from api.models import FuelStop


BASE_DIR = settings.BASE_DIR
FUEL_FILE = os.path.join(BASE_DIR, "fuel-prices-for-be-assessment.csv")


class Command(BaseCommand):
    help = 'Imports fuel stops from CSV, deduplicates and saves to database'

    def handle(self, *args, **options):
        """Imports fuel data from csv file"""

        self.stdout.write(self.style.WARNING("Adding fuel stops to database..."))

        unique_truckstops = {}

        with open(FUEL_FILE, "r") as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    opis_id = int(row["OPIS Truckstop ID"])
                    price = float(row["Retail Price"])

                    # If id exists, only replace if the new price is lower
                    if opis_id in unique_truckstops:
                        if price < unique_truckstops[opis_id]["retail_price"]:
                            unique_truckstops[opis_id] = row
                            unique_truckstops[opis_id]["retail_price"] = price
                    else:
                        unique_truckstops[opis_id] = row
                        unique_truckstops[opis_id]["retail_price"] = price
                except (ValueError, KeyError):
                    continue

        total_unique = len(unique_truckstops)
        stops_to_save = []
        for opis_id, data in unique_truckstops.items():
            stops_to_save.append(
                FuelStop(
                    opis_truckstop_id=opis_id,
                    truckstop_name=data["Truckstop Name"].strip(),
                    address=data["Address"].strip(),
                    city=data["City"].strip(),
                    state=data["State"].strip(),
                    rack_id=data["Rack ID"],
                    retail_price=data["Retail Price"],
                )
            )

        FuelStop.objects.all().delete()
        with transaction.atomic():
            FuelStop.objects.bulk_create(stops_to_save)

        self.stdout.write(self.style.SUCCESS(f"Saved {total_unique} unique stops."))
