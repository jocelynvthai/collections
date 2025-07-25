import json
import streamlit as st
import pandas as pd


def get_service_account_info(local=False):
    if local:
        service_account_info = st.secrets["gcp_service_account"]
    else: 
        with open('/gcp_service_account/GCLOUD_SERVICE_ACCOUNT', 'r') as f:
            service_account_info = json.load(f)
    return service_account_info


@st.cache_data
def get_invitation_homes_data(_credentials):
    query = """
        SELECT 
            *,
            DATE(pull_timestamp) AS pull_date
        FROM `homevest-data.sfr_rental_listings.invh_raw`
        ORDER BY property_id, pull_timestamp
    """
    # Load raw data
    ih_raw_df = pd.read_gbq(query, credentials=_credentials)
    ih_property_df = parse_properties(ih_raw_df)
    ih_lease_terms_df = parse_lease_terms(ih_raw_df)

    return ih_property_df, ih_lease_terms_df


def parse_properties(ih_raw_data):
    ih_property_raw_data = pd.json_normalize(
        ih_raw_data['data'].apply(json.loads),
        sep='_'
    )
    ih_property_raw_data['pull_date'] = ih_raw_data['pull_date']
    columns = [
        'pull_date', 
        'property_id', 
        'slug', 
        'market_name',
        'address_address_1',
        'address_city',
        'address_state',
        'address_zip_code',
        'map_location_latitude',
        'map_location_longitude',
        'status', 
        'available_on',
        'beds', 
        'baths', 
        'square_footage',
        'rent', 
        'total_monthly_rent',
        'is_application_enabled', 
        'is_self_show_enabled',
        'is_new_construction', 
        'is_on_special',
        'is_btr_community', 
        'is_exclusive',
        'is_featured_listing', 
        'is_model_home',
        'has_virtual_tour', 
        'application_url'
        ]
    ih_property_data = ih_property_raw_data[columns]

    # Convert types
    numeric_cols = ['beds', 'baths', 'square_footage', 'rent', 'total_monthly_rent']
    for col in numeric_cols:
        ih_property_data[col] = pd.to_numeric(ih_property_data[col])

    ih_property_data['available_on'] = pd.to_datetime(ih_property_data['available_on']).dt.tz_localize(None).dt.date
    
    return ih_property_data


def parse_lease_terms(ih_raw_data):
    ih_lease_terms_data = pd.json_normalize(ih_raw_data.apply(
            lambda row: [
                {
                    'property_id': row.property_id,
                    'pull_date': row.pull_date,
                    **term
                } 
                for term in json.loads(row.data)['terms']
            ], axis=1
        ).explode()
    )
    return ih_lease_terms_data


def get_market_cycle_data(ih_property_df):
    # Get latest market cycle data
    df = ih_property_df.copy()
    row_id_group = ['slug', 'cycle_id']
    market_cycle_df = get_market_cycle(df)
    date_vacated_df = get_date_vacated(market_cycle_df, row_id_group)
    date_available_df = get_date_available(date_vacated_df, row_id_group)

    grouped_df = date_available_df.groupby(['slug', 'cycle_id', 'property_id'])
    ih_property_cycle_df = pd.DataFrame({
        'market_name': grouped_df['market_name'].last(), 
        'address': grouped_df['address_address_1'].last(), 
        'city': grouped_df['address_city'].last(), 
        'state': grouped_df['address_state'].last(), 
        'zip_code': grouped_df['address_zip_code'].last(), 
        'beds': grouped_df['beds'].last(), 
        'baths': grouped_df['baths'].last(), 
        'square_footage': grouped_df['square_footage'].last(),
        'first_pull_date': grouped_df['pull_date'].first(),
        'last_pull_date': grouped_df['pull_date'].last(), 
        "latest_status": grouped_df['status'].last(),
        "date_vacated": grouped_df['date_vacated'].last(),
        'date_available': grouped_df['date_available'].last(),
        "available_on": grouped_df['available_on'].last(),
        'beginning_rent': grouped_df['rent'].first(),
        'latest_rent': grouped_df['rent'].last(), 
        "beginning_total_monthly_rent": grouped_df['total_monthly_rent'].first(),
        "latest_total_monthly_rent": grouped_df['total_monthly_rent'].last()
    }).reset_index()

    today = pd.to_datetime('today').normalize()
    ih_property_cycle_df['days_on_turn'] = (
        pd.to_datetime(ih_property_cycle_df['available_on'].fillna(pd.Timestamp.today())) - 
        pd.to_datetime(ih_property_cycle_df['date_vacated'])
    ).dt.days
    ih_property_cycle_df['vacant_leased'] = ih_property_cycle_df['last_pull_date'].apply(
        lambda pull_date: (pd.Timestamp(pull_date) + pd.Timedelta(days=1)).date() if pd.Timestamp(pull_date) < today else None
    )
    ih_property_cycle_df['days_on_market'] = (
        pd.to_datetime(ih_property_cycle_df['vacant_leased'].fillna(pd.Timestamp.today())) - 
        pd.to_datetime(ih_property_cycle_df['available_on'])
    ).dt.days
    
    return ih_property_cycle_df


def get_market_cycle(ih_property_df):
    """ Filter out rows for previous on market cycles """
    market_cycle_df = ih_property_df.copy()
    # Calculate date gaps
    market_cycle_df['prev_date'] = market_cycle_df.groupby('slug')['pull_date'].shift()
    market_cycle_df['gap'] = (market_cycle_df['pull_date'] - market_cycle_df['prev_date']).dt.days

    # Mark cycle id
    market_cycle_df['new_cycle'] = (market_cycle_df['gap'] > 14) | market_cycle_df['gap'].isna()
    market_cycle_df['cycle_id'] = market_cycle_df.groupby('slug')['new_cycle'].cumsum()

    return market_cycle_df[list(ih_property_df.columns) + ['cycle_id']]


def get_date_vacated(ih_property_df, row_id_group):
    """ Date status turned from 'Notice Unrented' to 'Vacant Unrented Not Ready' """
    date_vacated_df = ih_property_df.copy()

    # Find rows where status changed from 'Notice Unrented' to 'Vacant Unrented Not Ready'
    date_vacated_df['prev_status'] = date_vacated_df.groupby(row_id_group)['status'].shift()
    date_vacated_df['date_vacated_bool'] = (date_vacated_df['status'] == 'Vacant Unrented Not Ready') & (date_vacated_df['prev_status'] == 'Notice Unrented')

    # Get date vacated
    vacated_dates = (
        date_vacated_df[date_vacated_df['date_vacated_bool']]
        .groupby(row_id_group)['pull_date']
        .last()
        .rename('date_vacated')
    )
    date_vacated_df = date_vacated_df.merge(vacated_dates, on=row_id_group, how='left')
    return date_vacated_df[list(ih_property_df.columns) + ['date_vacated']]


def get_date_available(ih_property_df, row_id_group):
    """ Date status turned from 'Notice Unrented' to 'Vacant Unrented Not Ready' """
    date_available_df = ih_property_df.copy()

    # Find rows where status changed from 'Notice Unrented' to 'Vacant Unrented Not Ready'
    date_available_df['prev_status'] = date_available_df.groupby(row_id_group)['status'].shift()
    date_available_df['date_available_bool'] = (date_available_df['status'] == 'Vacant Unrented Ready') & (date_available_df['prev_status'] == 'Vacant Unrented Not Ready')

    # Get date available
    available_dates = (
        date_available_df[date_available_df['date_available_bool']]
        .groupby(row_id_group)['pull_date']
        .last()
        .rename('date_available')
    )
    date_available_df = date_available_df.merge(available_dates, on=row_id_group, how='left')
    return date_available_df[list(ih_property_df.columns) + ['date_available']]





