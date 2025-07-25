import json
import math
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

class Config:
    # Base URLs and endpoints
    MAIN_URL = "https://www.amh.com"
    API_BASE_URL = "https://www.amh.com/_next/data/{build_id}/query.json"

    # States for criteria (lowercase, hyphenated where needed)
    STATES = [
        'arizona', 'colorado', 'washington', 'florida', 'georgia', 'idaho', 'nevada',
        'north-carolina', 'ohio', 'south-carolina', 'tennessee', 'texas', 'utah'
    ]
    
    # BigQuery configuration
    PROJECT_ID = 'homevest-data'
    DATASET_ID = 'sfr_rental_listings'
    TABLE_ID = f'{PROJECT_ID}.{DATASET_ID}.amh_raw'
    
    # Default API parameters
    DEFAULT_PAGE_SIZE = 24


def get_build_id():
    """Dynamically fetch the build_id from AMH website"""
    try:
        response = requests.get(Config.MAIN_URL)
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

def setup_bigquery():
    """Initialize BigQuery table if it doesn't exist"""
    client = bigquery.Client(project=Config.PROJECT_ID)
    schema = [
        bigquery.SchemaField("property_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("pull_timestamp", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("data", "JSON", mode="NULLABLE"),
    ]
    
    try:
        client.get_table(Config.TABLE_ID)
        print(f"Table {Config.TABLE_ID} already exists.")
    except NotFound:
        print(f"Creating table {Config.TABLE_ID} with JSON schema...")
        table = bigquery.Table(Config.TABLE_ID, schema=schema)
        client.create_table(table)
        print(f"Table {Config.TABLE_ID} created with JSON schema.")
    
    return client

def fetch_properties(build_id, state, page):
    """Fetch properties from API for given state and page"""
    url = Config.API_BASE_URL.format(build_id=build_id)
    params = {
        'criteria': state,
        'viewType': 'grid',
        'page': page
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def process_properties(props, pull_timestamp, inserted_ids):
    """Process properties and prepare them for insertion"""
    new_props_to_insert = []
    for prop in props:
        prop_id = prop.get('id')
        if prop_id and prop_id not in inserted_ids:
            prop['pull_timestamp'] = pull_timestamp
            row = {
                "property_id": prop_id,
                "pull_timestamp": pull_timestamp,
                "data": json.dumps(prop)
            }
            new_props_to_insert.append(row)
            inserted_ids.add(prop_id)
    return new_props_to_insert

def main():
    # Initialize
    build_id = get_build_id()
    if not build_id:
        raise ValueError("Could not retrieve build ID")
    print(f"Build ID: {build_id}")
    
    client = setup_bigquery()
    pull_timestamp = datetime.now(timezone.utc).isoformat()
    inserted_ids = set()
    total_inserted = 0
    
    for state in Config.STATES:
        try:
            # Get initial page to determine total count
            data = fetch_properties(build_id, state, 1)
            count = data.get('pageProps', {}).get('count', 0)
            page_size = data.get('pageProps', {}).get('pageSize', Config.DEFAULT_PAGE_SIZE)
            num_pages = math.ceil(count / page_size) if page_size > 0 else 0
            
            print(f"\nState {state}: total {count} properties, page size {page_size}, {num_pages} pages")
            
            state_inserted = 0
            for page in range(1, num_pages + 1):
                try:
                    data = fetch_properties(build_id, state, page)
                    props = data.get('pageProps', {}).get('results', [])
                    
                    new_props = process_properties(props, pull_timestamp, inserted_ids)
                    
                    if new_props:
                        errors = client.insert_rows_json(Config.TABLE_ID, new_props)
                        if errors:
                            print(f"Errors while inserting batch for {state} page {page}: {errors}")
                        else:
                            batch_size = len(new_props)
                            total_inserted += batch_size
                            state_inserted += batch_size
                            print(f"Page {page}: Inserted {batch_size} properties (state total: {state_inserted})")
                    
                except (requests.RequestException, json.JSONDecodeError) as e:
                    print(f"Error processing {state} page {page}: {e}")
                    continue
                    
            print(f"Completed {state}: {state_inserted} properties inserted")
            
        except Exception as e:
            print(f"Error processing state {state}: {e}")
            continue
    
    print(f"\nTotal properties inserted: {total_inserted}")

if __name__ == "__main__":
    main()
