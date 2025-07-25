import json
from datetime import datetime, timezone
import time
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

class Config:
    # API and website configuration
    API_BASE_URL = "https://rentprogress.com/bin/progress-residential/property-search.state-{state}.page-1.rows-10000.nr-1.json"
    MAIN_URL = 'https://rentprogress.com/houses-for-rent'

    # Continental US state abbreviations (48 states, excluding AK, HI)
    STATES = [
        'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'IA', 'ID', 'IL',
        'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME', 'MI', 'MN', 'MO', 'MS', 'MT',
        'NC', 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', 'NY', 'OH', 'OK', 'OR', 'PA',
        'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VA', 'VT', 'WA', 'WI', 'WV', 'WY'
    ]
    
    # BigQuery configuration
    PROJECT_ID = 'homevest-data'
    DATASET_ID = 'sfr_rental_listings'
    TABLE_ID = f'{PROJECT_ID}.{DATASET_ID}.progress_raw_test'
    
    # Selenium configuration
    CHROME_OPTIONS = [
        "--headless",
        "--disable-blink-features=AutomationControlled",
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    ]

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

def setup_selenium():
    """Initialize Selenium WebDriver with proper configuration"""
    options = Options()
    for option in Config.CHROME_OPTIONS:
        options.add_argument(option)
    
    driver = webdriver.Chrome(options=options)
    
    # Visit main page to set cookies
    try:
        driver.get(Config.MAIN_URL)
        print("Visited main page to set cookies.")
        time.sleep(5)
    except Exception as e:
        print(f"Error visiting main page: {e}")
    
    return driver

def fetch_properties(driver, state_abbr, is_first_request=False):
    """Fetch properties for a given state"""
    url = Config.API_BASE_URL.format(state=state_abbr.lower())
    try:
        driver.get(url)
        # Add longer wait for first request
        if is_first_request:
            time.sleep(10)
        else:
            time.sleep(5)  # Add a consistent wait time for other requests
            
        body = driver.find_element(By.TAG_NAME, "body").text
        data = json.loads(body)
        return data.get('results', []), data.get('recordsFound', 0)
    except json.JSONDecodeError as json_err:
        print(f"Invalid JSON response for state {state_abbr}: {json_err}")
        with open(f"error_response_{state_abbr}.txt", "w", encoding="utf-8") as f:
            f.write(body)
        print(f"Response saved to error_response_{state_abbr}.txt for debugging")
        return [], 0
    except Exception as e:
        print(f"Error for state {state_abbr}: {e}")
        return [], 0

def main():
    client = setup_bigquery()
    driver = setup_selenium()
    
    pull_timestamp = datetime.now(timezone.utc).isoformat()
    unique_properties = {}
    inserted_ids = set()
    total_inserted = 0
    
    try:
        for i, state_abbr in enumerate(Config.STATES):
            props, count = fetch_properties(driver, state_abbr, is_first_request=(i==0))
            current_count = len(props)
            print(f"Fetched for state {state_abbr}: got {current_count} properties, total available: {count}")
            
            new_props_to_insert = []
            for prop in props:
                prop_id = prop.get('propertyId')
                if prop_id and prop_id not in unique_properties:
                    unique_properties[prop_id] = prop
                    if prop_id not in inserted_ids:
                        row = {
                            "property_id": prop_id,
                            "pull_timestamp": pull_timestamp,
                            "data": json.dumps(prop)
                        }
                        new_props_to_insert.append(row)
                        inserted_ids.add(prop_id)
            
            if new_props_to_insert:
                errors = client.insert_rows_json(Config.TABLE_ID, new_props_to_insert)
                if errors:
                    print(f"Encountered errors while inserting batch for state {state_abbr}: {errors}")
                else:
                    batch_size = len(new_props_to_insert)
                    total_inserted += batch_size
                    print(f"Successfully inserted {batch_size} new unique properties for state {state_abbr} "
                          f"(total inserted so far: {total_inserted})")
            
            print(f"Completed collection for state {state_abbr} (total unique so far: {len(unique_properties)})")
    
    finally:
        driver.quit()
    
    print(f"Successfully inserted a total of {total_inserted} unique properties to {Config.TABLE_ID}")

if __name__ == "__main__":
    main()