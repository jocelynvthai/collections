import json
import requests
import csv
from datetime import datetime, timezone

# Configuration
class Config:
    API_BASE_URL = "https://www.invitationhomes.com/property/api/geo-search"
    DELTA_LAT = 12.5
    DELTA_LONG = 29.1
    CSV_PATH = 'src/invh/invh.csv'
    
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

def setup_csv():
    """Initialize CSV file with headers"""
    fieldnames = ['property_id', 'pull_timestamp', 'data']
    with open(Config.CSV_PATH, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

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
    setup_csv()
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
                    with open(Config.CSV_PATH, 'a', newline='') as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=['property_id', 'pull_timestamp', 'data'])
                        writer.writerows(new_props)
                
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