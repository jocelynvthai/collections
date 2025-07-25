import json
import requests
from datetime import datetime, timezone
from google.cloud import bigquery
from google.cloud.exceptions import NotFound

# Configuration
class Config:
    API_BASE_URL = "https://www.invitationhomes.com/property/api/geo-search"
    DELTA_LAT = 12.5
    DELTA_LONG = 29.1
    
    # BigQuery configuration
    PROJECT_ID = 'homevest-data'
    DATASET_ID = 'sfr_rental_listings'
    TABLE_ID = f'{PROJECT_ID}.{DATASET_ID}.invh_raw'
    
    API_PARAMS = {
        'baths_min': 1,
        'beds_min': 1,
        'rent_min': 0,
        'rent_max': 10000,
        'sqft_min': 0,
        'sqft_max': 10000,
        'sort': 'distance',
        'sort_direction': 'asc',
        'limit': 20,
    }
    
    MARKETS = {
        'US': (36.8904, -95.9673),
    }

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

def fetch_properties(lat, lng, offset=0):
    """Fetch properties from API for given coordinates"""
    params = Config.API_PARAMS.copy()
    params.update({
        'south': lat - Config.DELTA_LAT,
        'west': lng - Config.DELTA_LONG,
        'north': lat + Config.DELTA_LAT,
        'east': lng + Config.DELTA_LONG,
        'lat': lat,
        'long': lng,
        'offset': offset,
    })
    
    response = requests.get(Config.API_BASE_URL, params=params)
    response.raise_for_status()
    return response.json()

def main():
    client = setup_bigquery()
    pull_timestamp = datetime.now(timezone.utc).isoformat()
    inserted_ids = set()
    
    for market, (lat, lng) in Config.MARKETS.items():
        offset = 0
        market_inserted_ids = set()
        while True:
            try:
                data = fetch_properties(lat, lng, offset)
                props = data.get('properties', [])
                total = data.get('total', 0) if offset == 0 else max(total, data.get('total', 0))
                
                new_props = []
                for prop in props:
                    prop_id = prop.get('property_id')
                    if prop_id and prop_id not in inserted_ids:
                        prop['pull_timestamp'] = pull_timestamp
                        new_props.append({
                            "property_id": prop_id,
                            "pull_timestamp": pull_timestamp,
                            "data": json.dumps(prop)
                        })
                        inserted_ids.add(prop_id)
                        market_inserted_ids.add(prop_id)
                
                if new_props:
                    errors = client.insert_rows_json(Config.TABLE_ID, new_props)
                    if errors:
                        print(f"Errors while inserting batch at offset {offset}: {errors}")
                
                print(f"Offset: {offset}, Total: {total}, Inserted: {len(new_props)}, Total Inserted: {len(inserted_ids)}")

                if offset + len(props) >= total or not props:
                    break
                offset += data.get('limit', Config.API_PARAMS['limit'])
                
            except (requests.RequestException, json.JSONDecodeError) as e:
                print(f"Error processing {market} at offset {offset}: {e}")
                break
                
        print()
        print(f"Completed {market}: {len(market_inserted_ids)} unique properties")
    
    print()
    print(f"Total properties inserted: {len(inserted_ids)}")

if __name__ == "__main__":
    main()