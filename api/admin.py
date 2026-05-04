from django.contrib import admin

from .models import FuelStop


@admin.register(FuelStop)
class FuelStopAdmin(admin.ModelAdmin):
    list_display = (
        'truckstop_name', 
        'address',
        'city', 
        'state', 
        'retail_price', 
        'latitude', 
        'longitude',
    )
