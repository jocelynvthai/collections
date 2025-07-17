import streamlit as st
from google.oauth2 import service_account

from tabs.data import get_bad_debt_inputs_data, get_collections_curve_data
from tabs.data_tab import data_filters, late_collections_over_ar, ar_over_gpr
from tabs.ontime_collections_tab import ontime_collections_curve_filters, ontime_collections_curve, ontime_collections_drilldown
from tabs.late_collections_tab import late_collections_curve_filters, late_collections_curve, late_collections_drilldown
from tabs.bad_debt_tab import bad_debt_over_time_filters, bad_debt_over_time, bad_debt_projection

# Configure page layout
st.set_page_config(
    page_title="Collections Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    [data-testid="stMetricLabel"] div {
        font-size: .7rem !important;
    }
    [data-testid="stMetricValue"] div {
        font-size: 1.5rem !important;
    }
    </style>
""", unsafe_allow_html=True)
# Authenticate
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)

bad_debt_inputs = get_bad_debt_inputs_data(credentials)
collections_curve_data = get_collections_curve_data(credentials)

st.title("Collections Dashboard")
data, ontime_collections, late_collections, bad_debt = st.tabs(["Data", "On-Time Collections", "Late Collections", "Bad Debt"])
with data:
    filtered_bad_debt_inputs, selected_month_year = data_filters(bad_debt_inputs)
    late_collections_over_ar(filtered_bad_debt_inputs, selected_month_year)
    ar_over_gpr(filtered_bad_debt_inputs, selected_month_year)

with ontime_collections:
    ontime_collections_selected_fund = ontime_collections_curve_filters(collections_curve_data)
    ontime_collections_curve(collections_curve_data, ontime_collections_selected_fund)
    ontime_collections_drilldown(bad_debt_inputs, ontime_collections_selected_fund)

with late_collections:
    late_collections_selected_fund = late_collections_curve_filters(collections_curve_data)
    late_collections_curve(collections_curve_data, late_collections_selected_fund)
    late_collections_drilldown(bad_debt_inputs, late_collections_selected_fund)

with bad_debt:
    bad_debt_selected_fund = bad_debt_over_time_filters(bad_debt_inputs)
    bad_debt_over_time(bad_debt_inputs, bad_debt_selected_fund)
    bad_debt_projection(bad_debt_inputs, bad_debt_selected_fund)
    

