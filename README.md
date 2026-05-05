# Optimal Fuel Routing API

An optimized Django REST API that calculates the most cost-effective cross-country road trips. Given a start and finish location in the US, this API plots the geographic route, calculates fuel consumption, and identifies the cheapest gas stations along the highway to minimize the total cost of the trip.

## Features
* **Global Geocoding Validation:** Uses *OpenStreetMap (Nominatim)* to convert city names to coordinates, featuring custom validation to reject international cities with US counterparts.

* **High-Fidelity Routing:** Integrates with the *OSRM API* to generate accurate, highway-preferential turn-by-turn geometry.

* **Smart Fuel Logistics:** Assumes a 500-mile vehicle range and automatically plots fuel stops right before the tank empties, strictly querying stops within a 5-mile radius of the active route.

* **Instant Map Visualization:** Includes a custom Postman Visualizer script to render the 7,000+ point GeoJSON route and gas station markers natively in Postman.

---

## Technical Architecture & Optimizations

Calculating Haversine distances between a 200,000+ point OSRM route and a database of 6,700 gas stations requires ~1 billion mathematical operations. A naive nested loop takes **15+ seconds** to process. This API uses three core optimizations to bring response times down to **< 2 seconds**:

### 1. Dual-Track Geometry Downsampling
The massive OSRM coordinate array is downsampled into two separate lists:
* **Map Geometry (`[::10]`):** 200,000 to 20,000 points. Returned in the JSON payload to ensure the frontend renders a smooth, curve-accurate polyline on the map.

### 2. The "Micro-Box" Spatial Query
Instead of querying the database for all 6,700 stops or drawing one massive bounding box across the entire country (which captures thousands of irrelevant stops on diagonal trips), the API uses an "Odometric Micro-Box" search.
* The algorithm tracks the distance driven.
* At ~450 miles, it draws a tiny 10x10 mile bounding box (`latitude__range`, `longitude__range`) around the truck's exact coordinate.
* Utilizing `db_index=True` on the model coordinates, the database returns the 5-10 local gas stations in milliseconds.

### 3. Fast Pythagorean Approximation
For micro-distances (checking if a gas station is within 5 miles of the highway), the curvature of the earth is negligible. The API bypasses the computationally heavy trigonometric `math.sin` and `math.cos` calls of the Haversine formula, opting for a highly optimized Equirectangular approximation.

---

## API Usage

Make sure you've docker installed.
Run these commands to clone and start the server on http://localhost:8000/
```
git clone https://github.com/Xerx81/spotter.git
cd spotter
docker compose up -d --build
```

Run these commands to import data from csv file and store their coordinated using nominatim api (it might take +1hr due to the 1 req/s api limit) (even if u stop geocoding, it will resume from where it left off)
```
docker compose exec web python manage.py import_fuel_data
docker compose exec web python manage.py geocode
```

- **Endpoint:** `POST http://localhost:8000/

### Response (JSON)
```json
{
    "total_distance_miles": 1279.15,
    "duration_hours": 24.42,
    "total_fuel_cost": 424.50,
    "fuel_stops": [
        {
            "name": "Pilot Travel Center",
            "location": [-118.243, 34.052],
            "city": "Los Angeles",
            "state": "CA",
            "price_per_gallon": 3.15,
            "gallons_filled": 45.0,
            "stop_cost": 141.75
        },
        ...
    ],
    "route_geometry": [
        [-122.332, 47.606],
        [-122.331, 47.605],
        ...
    ]
}
```

### Test it out with Postman

Paste this in the body of the request:
```json
{"start_location": "New york", "end_location": "miami"}
```

Paste this in the scripts tab:
```
var template = `
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
</head>
<body style="margin: 0; padding: 0;">
    <div id="map" style="height: 100vh; width: 100vw;"></div>
    <script>
        // 1. Initialize Map
        var map = L.map('map').setView([39.8283, -98.5795], 4);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

        // 2. THE FIX: Ask Postman for the data asynchronously!
        pm.getData(function (error, data) {
            if (error) {
                document.getElementById('map').innerHTML = "<h3 style='color:red; padding:20px;'>Error fetching data: " + error + "</h3>";
                return;
            }

            // 3. Draw the Route using Native GeoJSON
            if (data.route_geometry && data.route_geometry.length > 0) {
                var geojsonFeature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": data.route_geometry // [lon, lat] format
                    }
                };

                var routeLayer = L.geoJSON(geojsonFeature, {
                    style: { color: '#FF5733', weight: 5, opacity: 0.9 } // Bright orange
                }).addTo(map);

                map.fitBounds(routeLayer.getBounds());
            }

            // 4. Draw the Fuel Stops
            if (data.fuel_stops && data.fuel_stops.length > 0) {
                data.fuel_stops.forEach(function(stop) {
                    var marker = L.marker([stop.location[1], stop.location[0]]).addTo(map);
                    marker.bindPopup("<b>" + stop.name + "</b><br/>" + stop.city + ", " + stop.state);
                });
            }
        });
    </script>
</body>
</html>
`;

// Pass the raw JSON response directly to the template
pm.visualizer.set(template, pm.response.json());
```

Click send and JSON tab will show the response and visualization tab will show the map like this below:

<img width="1537" height="511" alt="image" src="https://github.com/user-attachments/assets/b17fcfa3-a9c0-4658-8352-8dc4804b8c8d" />

