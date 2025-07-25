import json
import math
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# States for criteria (lowercase, hyphenated where needed)
states = [
    'arizona', 'colorado', 'washington', 'florida', 'georgia', 'idaho', 'nevada',
    'north-carolina', 'ohio', 'south-carolina', 'tennessee', 'texas', 'utah'
]

# Function to dynamically fetch the build_id
def get_build_id():
    url = "https://www.amh.com"
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        scripts = soup.find_all('script', src=True)
        for script in scripts:
            if '_buildManifest.js' in script['src']:
                parts = script['src'].split('/')
                build_id_index = parts.index('static') + 1
                return parts[build_id_index]
        raise ValueError("Build ID not found")
    except Exception as e:
        print(f"Error fetching build ID: {e}")
        return None

build_id = get_build_id()
if not build_id:
    raise ValueError("Could not retrieve build ID")

print(f"Build ID: {build_id}")

# API base URL template
base_url_template = "https://www.amh.com/_next/data/{build_id}/query.json?criteria={criteria}&viewType=grid&page={page}"

# BigQuery configuration
project_id = 'homevest-data'
dataset_id = 'sfr_rental_listings'
table_id = f'{project_id}.{dataset_id}.amh_raw'  # Full table ID

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

# Collect unique properties across all states (dict keyed by unique ID)
unique_properties = {}
inserted_ids = set()  # Track inserted to avoid any re-inserts

# Add timestamp once, for consistency across the entire pull
pull_timestamp = datetime.now(timezone.utc).isoformat()

total_inserted = 0

for state in states:
    # Fetch page 1 to get count and pageSize
    page1_url = base_url_template.format(build_id=build_id, criteria=state, page=1)
    try:
        response = requests.get(page1_url)
        response.raise_for_status()
        data = response.json()
        count = data.get('pageProps', {}).get('count', 0)
        page_size = data.get('pageProps', {}).get('pageSize', 24)  # Default to 24 if not found
    except requests.RequestException as e:
        print(f"API error for {state} page 1: {e}")
        continue
    except json.JSONDecodeError:
        print(f"Invalid JSON response for {state} page 1")
        continue
    
    num_pages = math.ceil(count / page_size) if page_size > 0 else 0
    print(f"State {state}: total {count} properties, page size {page_size}, {num_pages} pages")
    
    for page in range(1, num_pages + 1):
        url = base_url_template.format(build_id=build_id, criteria=state, page=page)
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            props = data.get('pageProps', {}).get('results', [])
        except requests.RequestException as e:
            print(f"API error for {state} page {page}: {e}")
            continue
        except json.JSONDecodeError:
            print(f"Invalid JSON response for {state} page {page}")
            continue
        
        current_count = len(props)
        print(f"Fetched for {state}: page {page}, got {current_count} properties, total available: {count}")
        
        new_props_to_insert = []
        for prop in props:
            prop_id = prop.get('id')
            if prop_id and prop_id not in unique_properties:
                prop['pull_timestamp'] = pull_timestamp  # Add to the data blob
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
                print(f"Encountered errors while inserting batch for {state} page {page}: {errors}")
            else:
                batch_size = len(new_props_to_insert)
                total_inserted += batch_size
                print(f"Successfully inserted {batch_size} new unique properties for {state} page {page} (total inserted so far: {total_inserted})")
    
    print(f"Completed collection for {state} (total unique so far: {len(unique_properties)})")

print(f"Successfully inserted a total of {total_inserted} unique properties to {table_id}")