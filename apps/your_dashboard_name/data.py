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
def get_data(_credentials):
    query = """
        SELECT * 
        FROM `_` 
    """
    data = pd.read_gbq(query, credentials=_credentials)
    return data

