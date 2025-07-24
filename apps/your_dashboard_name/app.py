import streamlit as st
from google.oauth2 import service_account

from data import get_service_account_info, get_data

# Configure page layout
st.set_page_config(
    page_title="Dashboard Name",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Data Retrieval
credentials = service_account.Credentials.from_service_account_info(get_service_account_info(local=True))
invitation_homes_data = get_data(credentials)

# Application
st.title("Dashboard Name")
