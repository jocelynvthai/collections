import streamlit as st
import altair as alt
from datetime import datetime
from dateutil.relativedelta import relativedelta

def date_month_filter(key):
    current_date = datetime.now()
    month_year_options = []

    for i in range(12):
        date = (current_date - relativedelta(months=i)).replace(day=1)
        month_year_options.append(date.strftime("%B %Y"))

    return st.selectbox(
        "Select a month",
        month_year_options,
        key=key
        )

def fund_filter(key, data, include_all=False):
    values = sorted(set(data['fund'].unique().tolist()))
    if include_all:
        values = ['All'] + values
    return st.selectbox(
        "Select a fund",
        values,
        key=key
    )

# Color and dash mapping
color_scale = alt.Scale(domain=[
    'Last Month',
    'Last 3 Months',
    'Last 12 Months',
    'This Month Succeeded',
    'This Month Paid'
], range=[
    '#d1c4e9',  # soft lavender (Last Month)
    '#9575cd',  # light-medium purple (Last 3 Months)
    '#512da8',  # deep purple (Last 12 Months)
    '#15b8a6',  # teal (This Month Succeeded)
    '#15b8a6'   # teal (This Month Paid, dotted)
])

dash_scale = alt.Scale(domain=[
    'Last Month',
    'Last 3 Months',
    'Last 12 Months',
    'This Month Succeeded',
    'This Month Paid'
], range=[
    [1,0],      # solid
    [1,0],      # solid
    [1,0],      # solid
    [1,0],      # solid
    [4,4]       # dotted
])