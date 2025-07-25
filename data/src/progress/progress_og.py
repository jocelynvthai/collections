import json
from datetime import datetime, timezone
import time
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Continental US state abbreviations (48 states, excluding AK, HI)
states = [
    'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'IA', 'ID', 'IL',
    'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME', 'MI', 'MN', 'MO', 'MS', 'MT',
    'NC', 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', 'NY', 'OH', 'OK', 'OR', 'PA',
    'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VA', 'VT', 'WA', 'WI', 'WV', 'WY'
    
]

# API base URL template
base_url_template = "https://rentprogress.com/bin/progress-residential/property-search.state-{state}.page-1.rows-10000.nr-1.json"

# BigQuery configuration
project_id = 'homevest-data'
dataset_id = 'sfr_rental_listings'
table_id = f'{project_id}.{dataset_id}.progress_raw_test'  # Full table ID

# Define schema with JSON column for dynamic fields
schema = [
    bigquery.SchemaField("property_id", "STRING", mode="NULLABLE"),  # For uniqueness/queries
    bigquery.SchemaField("pull_timestamp", "STRING", mode="NULLABLE"),  # ISO datetime
    bigquery.SchemaField("data", "JSON", mode="NULLABLE"),  # Holds entire property blob dynamically
]

# Create BigQuery client
client = bigquery.Client(project=project_id)

# Check if table exists; create if not, with JSON schema
try:
    client.get_table(table_id)
    print(f"Table {table_id} already exists.")
except NotFound:
    print(f"Creating table {table_id} with JSON schema for dynamic fields...")
    table = bigquery.Table(table_id, schema=schema)
    client.create_table(table)
    print(f"Table {table_id} created with JSON schema.")

# Set up Selenium with Chromium
options = Options()
options.add_argument("--headless")  # Run headless
options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid bot detection
options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
driver = webdriver.Chrome(options=options)

# Visit main page to set cookies
try:
    driver.get('https://rentprogress.com/houses-for-rent')
    print("Visited main page to set cookies.")
    time.sleep(5)
except Exception as e:
    print(f"Error visiting main page: {e}")

# Collect unique properties across all states (dict keyed by unique ID)
unique_properties = {}
inserted_ids = set()  # Track inserted to avoid any re-inserts

# Add timestamp once, for consistency across the entire pull
pull_timestamp = datetime.now(timezone.utc).isoformat()

total_inserted = 0
count = 0
for state_abbr in states:
    url = base_url_template.format(state=state_abbr.lower())
    try:
        driver.get(url)
        if count == 0:
            time.sleep(10)
            count += 1
        # Get the JSON from the pre tag or body
        body = driver.find_element(By.TAG_NAME, "body").text
        # Save response to file for debugging if JSON parsing fails
        try:
            data = json.loads(body)
        except json.JSONDecodeError as json_err:
            print(f"Invalid JSON response for state {state_abbr}: {json_err}")
            with open(f"error_response_{state_abbr}.txt", "w", encoding="utf-8") as f:
                f.write(body)
            print(f"Response saved to error_response_{state_abbr}.txt for debugging")
            continue
        props = data.get('results', [])
        count = data.get('recordsFound', 0)
    except Exception as e:
        print(f"Error for state {state_abbr}: {e}")
        continue
    
    current_count = len(props)
    print(f"Fetched for state {state_abbr}: got {current_count} properties, total available: {count}")
    
    new_props_to_insert = []
    for prop in props:
        prop_id = prop.get('propertyId')
        if prop_id and prop_id not in unique_properties:
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
            print(f"Encountered errors while inserting batch for state {state_abbr}: {errors}")
        else:
            batch_size = len(new_props_to_insert)
            total_inserted += batch_size
            print(f"Successfully inserted {batch_size} new unique properties for state {state_abbr} (total inserted so far: {total_inserted})")
    
    print(f"Completed collection for state {state_abbr} (total unique so far: {len(unique_properties)})")

driver.quit()

print(f"Successfully inserted a total of {total_inserted} unique properties to {table_id}")