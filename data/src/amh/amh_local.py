import json
import math
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
import csv
import os

class Config:
    MAIN_URL = "https://www.amh.com"
    API_URL_TEMPLATE = "https://www.amh.com/_next/data/{build_id}/query.json"
    CSV_PATH = 'src/amh/amh_properties.csv'

    # States for criteria (lowercase, hyphenated where needed)
    STATES = [
        'arizona', 'colorado', 'washington', 'florida', 'georgia', 'idaho', 'nevada',
        'north-carolina', 'ohio', 'south-carolina', 'tennessee', 'texas', 'utah'
    ]
    
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

def setup_csv():
    """Setup CSV file with headers"""
    headers = [
        'property_id',
        'pull_timestamp',
        'state',
        'address',
        'city',
        'zip_code',
        'bedrooms',
        'bathrooms',
        'square_feet',
        'monthly_rent',
        'latitude',
        'longitude',
        'url'
    ]
    
    with open(Config.CSV_PATH, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
    

def fetch_properties(build_id, state, page):
    """Fetch properties from API for given state and page"""
    url = Config.API_URL_TEMPLATE.format(build_id=build_id)
    params = {
        'criteria': state,
        'viewType': 'grid',
        'page': page
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def process_properties(props, pull_timestamp, state, inserted_ids, csv_path):
    """Process properties and write them to CSV"""
    new_props_count = 0
    with open(csv_path, 'a', newline='') as f:
        writer = csv.writer(f)
        for prop in props:
            prop_id = prop.get('id')
            if prop_id and prop_id not in inserted_ids:
                # Extract relevant data from property
                row = [
                    prop_id,
                    pull_timestamp,
                    state,
                    prop.get('address', ''),
                    prop.get('city', ''),
                    prop.get('zipCode', ''),
                    prop.get('beds', ''),
                    prop.get('baths', ''),
                    prop.get('sqft', ''),
                    prop.get('price', ''),
                    prop.get('latitude', ''),
                    prop.get('longitude', ''),
                    f"{Config.MAIN_URL}/properties/{prop_id}"
                ]
                writer.writerow(row)
                inserted_ids.add(prop_id)
                new_props_count += 1
    return new_props_count

def main():
    # Initialize
    build_id = get_build_id()
    if not build_id:
        raise ValueError("Could not retrieve build ID")
    print(f"Build ID: {build_id}")
    
    setup_csv()
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
                    
                    new_props_count = process_properties(props, pull_timestamp, state, inserted_ids, Config.CSV_PATH)
                    total_inserted += new_props_count
                    state_inserted += new_props_count
                    print(f"Page {page}: Added {new_props_count} properties (state total: {state_inserted})")
                    
                except (requests.RequestException, json.JSONDecodeError) as e:
                    print(f"Error processing {state} page {page}: {e}")
                    continue
                    
            print(f"Completed {state}: {state_inserted} properties added")
            
        except Exception as e:
            print(f"Error processing state {state}: {e}")
            continue
    
    print(f"\nTotal properties added to CSV: {total_inserted}")
    print(f"CSV file saved at: {Config.CSV_PATH}")

if __name__ == "__main__":
    main()
