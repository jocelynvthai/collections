import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
import numpy as np


def invh_filters(ih_property_cycle_df):
    col_date_range, col_market = st.columns(2)

    ih_property_period_df = ih_property_cycle_df.copy()
    with col_date_range:
        date_range = st.date_input("Pick a period range", 
                                value=(datetime.now() - timedelta(days=1),  datetime.now()), 
                                format='MM/DD/YYYY')
        if len(date_range) != 2:
            st.stop()
        else: 
            start_date, end_date = date_range[0], date_range[1]
            ih_property_period_df = ih_property_period_df[(ih_property_period_df['first_pull_date'] <= end_date) & 
                                                        (ih_property_period_df['last_pull_date'] >= start_date)]
    with col_market:
        selected_market = st.selectbox("Select a market", 
                                options=['All'] + list(ih_property_cycle_df['market_name'].unique()), index=0)
        if selected_market != 'All':
            ih_property_period_df = ih_property_period_df[ih_property_period_df['market_name'] == selected_market]

    return ih_property_period_df, start_date, end_date



def clearance_rates(ih_property_period_df, start_date, end_date):
    st.subheader("Clearance Rates")

    prelease_df = ih_property_period_df[ih_property_period_df['latest_status'].isin(['Notice Unrented', 'Vacant Unrented Not Ready'])]
    rent_ready_df = ih_property_period_df[ih_property_period_df['latest_status'].isin(['Vacant Unrented Ready'])]
    clearance_rates = [
        len(prelease_df[(prelease_df['vacant_leased']>=start_date) & (prelease_df['vacant_leased']<=end_date)])*100 / len(prelease_df), 
        len(rent_ready_df[(rent_ready_df['vacant_leased']>=start_date) & (rent_ready_df['vacant_leased']<=end_date)])*100 / len(rent_ready_df)
    ]
    col_prelease_clearance_rate, col_rent_ready_clearance_rate = st.columns(2)
    with col_prelease_clearance_rate:
        st.metric("Pre-lease Clearance Rate", f"{clearance_rates[0]:.2f}%", help="% of pre-lease homes (Notice Unrented, Vacant Unrented Not Ready) rented in period range")
    with col_rent_ready_clearance_rate:
        st.metric("Rent Ready Clearance Rate", f"{clearance_rates[1]:.2f}%", help="% of pre-lease homes (Vacant Unrented Ready) rented in period range")


def homes_rented_stats(ih_property_period_df, start_date, end_date):
    st.subheader("Homes Rented Stats")

    homes_rented_df = ih_property_period_df[ih_property_period_df['vacant_leased'].notna()]
    
    # Rent scatter plot
    if len(homes_rented_df['market_name'].unique()) == 1:
        color_scale = alt.Scale(range=['#15b8a6']) 
    else:
        color_scale = alt.Scale(scheme='tealblues')  
    scatter_chart = alt.Chart(homes_rented_df).mark_point().encode(
        x=alt.X('beginning_rent:Q', title='Beginning Rent'),
        y=alt.Y('latest_rent:Q', title='Latest Rent'),
        color=alt.Color('market_name:N', scale=color_scale, title='Market'),
        tooltip=['market_name', 'beginning_rent', 'latest_rent']
    )
    diagonal_line = alt.Chart(pd.DataFrame({
        'x': [0, homes_rented_df['beginning_rent'].max()],
        'y': [0, homes_rented_df['beginning_rent'].max()]
    })).mark_line(color='#00000010').encode(x='x:Q', y='y:Q')
    st.altair_chart((diagonal_line + scatter_chart).properties(title='Market Cycle Rent Comparison'), use_container_width=True)

    # Days on Market strip plot
    dom_strip = alt.Chart(homes_rented_df).mark_point().encode(
        x=alt.X('days_on_market:Q', title='# Days'),
        y=alt.Y('market_name:N', title=None),
        color=alt.Color('market_name:N', scale=color_scale, title='Market', legend=None),
        tooltip=['market_name', 'days_on_market', 'address']
    ).properties(
        title='Days on Market'
    )

    st.altair_chart(dom_strip, use_container_width=True)

    st.dataframe(homes_rented_df[['address', 'city', 'state', 'market_name', 
                                  'first_pull_date', 'last_pull_date', 'latest_status', 
                                  'available_on', 'date_vacated', 'beginning_rent', 'latest_rent', 
                                  'beginning_total_monthly_rent', 'latest_total_monthly_rent', 
                                  'vacant_leased', 'days_on_market']])
    






















