import hashlib
import json
from datetime import datetime
import pytz

import requests
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# List of all current markets with central coordinates (lat, long in decimal degrees)
markets = {
    # 'Atlanta': (33.7490, -84.3880),
    # 'Austin': (30.2672, -97.7431),
    # 'Carolinas': (35.2271, -80.8431),
    # 'Chicago': (41.8781, -87.6298),
    # 'Dallas': (32.7767, -96.7970),
    # 'Denver': (39.7392, -104.9903),
    # 'Houston': (29.7604, -95.3698),
    # 'Jacksonville': (30.3322, -81.6557),
    # 'Las Vegas': (36.1699, -115.1398),
    # 'Minneapolis': (44.9778, -93.2650),
    # 'Nashville': (36.1627, -86.7816),
    # 'Northern California': (38.5816, -121.4944),
    # 'Orlando': (28.5383, -81.3792),
    # 'Phoenix': (33.4484, -112.0740),
    # 'San Antonio': (29.4241, -98.4936),
    # 'Seattle': (47.6062, -122.3321),
    # 'South Florida/Miami': (25.7617, -80.1918),
    # 'Southern California': (34.0522, -118.2437),
    # 'Tampa': (27.9506, -82.4572),
    'US': (36.8904, -95.9673),
}

# Bounding box deltas (degrees)
delta_lat = 12.5
delta_long = 29.1

# API base URL and fixed parameters
base_url = "https://www.invitationhomes.com/property/api/geo-search"
fixed_params = {
    'baths_min': 1,
    'beds_min': 1,
    'rent_min': 0,
    'rent_max': 10000,
    'sqft_min': 0,
    'sqft_max': 10000,
    'sort': 'distance',
    'sort_direction': 'asc',
    'limit': 20,  # Adjust to 20 if API enforces a lower max
}

# BigQuery configuration (replace with your values)
project_id = 'homevest-data'
dataset_id = 'sfr_rental_listings'
table_id = f'{project_id}.{dataset_id}.invh_raw'  # Full table ID

# Define schema with JSON column for dynamic fields
schema = [
    bigquery.SchemaField("property_id", "STRING", mode="NULLABLE"),  # For uniqueness/queries
    bigquery.SchemaField("pull_timestamp", "STRING", mode="NULLABLE"),  # ISO datetime
    bigquery.SchemaField("data", "JSON", mode="NULLABLE"),  # Holds entire property blob dynamically
]

# Create BigQuery client
client = bigquery.Client()

# Check if table exists; create if not, with JSON schema
try:
    client.get_table(table_id)
    print(f"Table {table_id} already exists.")
except NotFound:
    print(f"Creating table {table_id} with JSON schema for dynamic fields...")
    table = bigquery.Table(table_id, schema=schema)
    client.create_table(table)
    print(f"Table {table_id} created with JSON schema.")

# Collect unique properties across all markets (dict keyed by unique ID)
unique_properties = {}
inserted_ids = set()  # Track inserted to avoid any re-inserts

# Add timestamp once, for consistency across the entire pull
pull_timestamp = datetime.now(pytz.timezone('America/New_York')).isoformat()

total_inserted = 0

for market, (lat, lng) in markets.items():
    south = lat - delta_lat
    north = lat + delta_lat
    west = lng - delta_long
    east = lng + delta_long
    
    offset = 0
    total = 0  # Will be updated from response
    while True:
        params = fixed_params.copy()
        params.update({
            'south': south,
            'west': west,
            'north': north,
            'east': east,
            'lat': lat,
            'long': lng,
            'offset': offset,
        })
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            props = data.get('properties', [])
            current_total = data.get('total', 0)
            current_limit = data.get('limit', fixed_params['limit'])
            current_offset = data.get('offset', offset)
        except requests.RequestException as e:
            print(f"API error for {market} at offset {offset}: {e}")
            break
        except json.JSONDecodeError:
            print(f"Invalid JSON response for {market} at offset {offset}")
            break
        
        # Update total if it's the first fetch or if it changes (though unlikely)
        if offset == 0:
            total = current_total
        else:
            total = max(total, current_total)  # In case it fluctuates, take max
        
        current_count = len(props)
        print(f"Fetched for {market}: offset {current_offset}, got {current_count} properties, total available: {total}")
        
        new_props_to_insert = []
        for prop in props:
            prop_id = prop.get('property_id')
            if prop_id and prop_id not in unique_properties:
                prop['pull_timestamp'] = pull_timestamp  # Add to the data blob
                # prop.pop('photos', None)  # Uncomment if needed
                # prop.pop('terms', None)   # Uncomment if needed
                unique_properties[prop_id] = prop
                if prop_id not in inserted_ids:
                    # Wrap for JSON column: extract key fields, stringify 'data' as JSON
                    row = {
                        "property_id": prop_id,
                        "pull_timestamp": pull_timestamp,
                        "data": json.dumps(prop)  # Convert dict to JSON string for the JSON column
                    }
                    new_props_to_insert.append(row)
                    inserted_ids.add(prop_id)
        
        # Insert the new unique properties from this batch
        if new_props_to_insert:
            errors = client.insert_rows_json(table_id, new_props_to_insert)
            if errors:
                print(f"Encountered errors while inserting batch at offset {offset}: {errors}")
            else:
                batch_size = len(new_props_to_insert)
                total_inserted += batch_size
                print(f"Successfully inserted {batch_size} new unique properties from offset {offset} (total inserted so far: {total_inserted})")
        
        if current_offset + current_count >= total or current_count == 0:
            break
        offset += current_limit  # Use the effective limit from response
    
    print(f"Completed collection for {market} (total unique so far: {len(unique_properties)})")

print(f"Successfully inserted a total of {total_inserted} unique properties to {table_id}")