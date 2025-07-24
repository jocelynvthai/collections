import streamlit as st
from google.oauth2 import service_account

from data import get_service_account_info, get_invitation_homes_data, get_market_cycle_data
from tabs.clearance_rates_tab import invh_filters, clearance_rates, homes_rented_stats

# Configure page layout
st.set_page_config(
    page_title="Leasing Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Data Retrieval
credentials = service_account.Credentials.from_service_account_info(get_service_account_info(local=True))
ih_property_df, ih_lease_terms_df = get_invitation_homes_data(credentials)
ih_property_cycle_df = get_market_cycle_data(ih_property_df)

# Application
st.title("Leasing Dashboard")

invh_tab, tab2 = st.tabs(["Invitation Homes", 'tab2'])
with invh_tab:
    ih_property_period_df, start_date, end_date = invh_filters(ih_property_cycle_df)
    clearance_rates(ih_property_period_df, start_date, end_date)
    homes_rented_stats(ih_property_period_df, start_date, end_date)
with tab2:
    st.write(ih_property_cycle_df)



