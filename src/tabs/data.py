import streamlit as st
import pandas as pd


@st.cache_data
def get_bad_debt_inputs_data(_credentials):
    bad_debt_inputs = pd.read_gbq(f"SELECT * \
                        FROM `homevest-data.dbt_kyanscienceman_tin.bad_debt_inputs` \
                        WHERE month >= DATE_SUB(LAST_DAY(CURRENT_DATE(), MONTH), INTERVAL 11 MONTH) \
                        AND month <= LAST_DAY(CURRENT_DATE(), MONTH)", credentials=_credentials)
    # Convert month to first of the month for charting purposes
    bad_debt_inputs['month'] = pd.to_datetime(bad_debt_inputs['month']).dt.to_period('M').dt.to_timestamp()
    bad_debt_inputs['display_month'] = bad_debt_inputs['month'].dt.strftime('%B %Y')
    return bad_debt_inputs


@st.cache_data
def get_collections_curve_data(_credentials):
    collections_curve_data = pd.read_gbq(f"SELECT * \
                        FROM `homevest-data.dbt_kyanscienceman_tin.rent_collections_curve`", credentials=_credentials)
    return collections_curve_data

