import math

from .models import FuelStop


def calculate_fuel(route_geometry: list, total_trip_distance: float):
    MAX_RANGE = 500
    BUFFER = 50
    TARGET_DRIVE_DISTANCE = MAX_RANGE - BUFFER
    
    optimal_stops = []
    total_fuel_cost = 0.0
    
    if total_trip_distance <= MAX_RANGE:
        return [], 0.0

    distance_since_last_stop = 0.0
    
    for i in range(1, len(route_geometry)):
        prev_point = route_geometry[i-1]
        curr_point = route_geometry[i]
        
        lon1, lat1 = prev_point
        lon2, lat2 = curr_point
        
        # Use the Pythagorean distance
        x = (lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2)) * 69.172
        y = (lat2 - lat1) * 69.172
        segment_dist = math.sqrt(x*x + y*y)
        
        distance_since_last_stop += segment_dist
        
        # Time to look for fuel!
        if distance_since_last_stop >= TARGET_DRIVE_DISTANCE:
            # Create a bounding box around the route coordinates
            margin = 0.1
            min_lat, max_lat = lat2 - margin, lat2 + margin
            min_lon, max_lon = lon2 - margin, lon2 + margin
            
            # Query the database ONLY for stops inside this box
            stops = list(
                FuelStop.objects.filter(
                    latitude__range=(min_lat, max_lat),
                    longitude__range=(min_lon, max_lon)
                ).values('truckstop_name', 'latitude', 'longitude', 'retail_price', 'city', 'state')
            )
            
            cheapest_stop = None
            lowest_price = float('inf')
            
            # Check the math only on the gas stations in this tiny box
            for stop in stops:
                stop_x = (stop['longitude'] - lon2) * math.cos(math.radians((lat2 + stop['latitude']) / 2)) * 69.172
                stop_y = (stop['latitude'] - lat2) * 69.172
                dist_to_stop = math.sqrt(stop_x*stop_x + stop_y*stop_y)
                
                if dist_to_stop <= 5.0:  # Must be within 5 miles
                    if stop['retail_price'] < lowest_price:
                        lowest_price = stop['retail_price']
                        cheapest_stop = stop
            
            if cheapest_stop:
                gallons_needed = distance_since_last_stop / 10.0
                cost = gallons_needed * cheapest_stop['retail_price']
                total_fuel_cost += cost
                
                optimal_stops.append({
                    "truckstop_name": cheapest_stop['truckstop_name'],
                    "location": [cheapest_stop['longitude'], cheapest_stop['latitude']],
                    "city": cheapest_stop['city'],
                    "state": cheapest_stop['state'],
                    "price_per_gallon": cheapest_stop['retail_price'],
                    "gallons_filled": round(gallons_needed, 2),
                    "stop_cost": round(cost, 2)
                })
                
                distance_since_last_stop = 0.0

    # Calculate final stretch
    if distance_since_last_stop > 0 and optimal_stops:
        final_gallons = distance_since_last_stop / 10.0
        total_fuel_cost += final_gallons * optimal_stops[-1]['price_per_gallon']

    return optimal_stops, total_fuel_cost
