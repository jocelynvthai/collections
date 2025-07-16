import streamlit as st
import altair as alt

from tabs.utils import date_month_filter, fund_filter


def data_filters(bad_debt_inputs):
    month_year, fund, rental_status, eviction_status = st.columns(4)
    with month_year:
        selected_month_year = date_month_filter(key='data_select_month_year')
    with fund:
        selected_fund = fund_filter(key='data_select_fund', data=bad_debt_inputs)
    with rental_status: 
        selected_rental_status = st.selectbox(
            "Select a rental status",
            ['All', 'In Home', 'Moved Out'],
        )
    with eviction_status:
        eviction_options = ['All', 'Yes', 'No']
        selected_eviction_status = st.selectbox(
            "Evicted?",
            eviction_options,
            disabled=selected_rental_status != 'Moved Out'
        )
    
    filtered_bad_debt_inputs = bad_debt_inputs.copy()
    if selected_fund != 'All':
        filtered_bad_debt_inputs = filtered_bad_debt_inputs[filtered_bad_debt_inputs['fund'] == selected_fund]

    if selected_rental_status == 'In Home':
        filtered_bad_debt_inputs = filtered_bad_debt_inputs[filtered_bad_debt_inputs['rental_status'] == 'active']
    elif selected_rental_status == 'Moved Out':
        filtered_bad_debt_inputs = filtered_bad_debt_inputs[filtered_bad_debt_inputs['rental_status'] != 'active']
    
    if selected_eviction_status == 'Yes':
        filtered_bad_debt_inputs = filtered_bad_debt_inputs[filtered_bad_debt_inputs['was_evicted'] == True]
    elif selected_eviction_status == 'No':
        filtered_bad_debt_inputs = filtered_bad_debt_inputs[filtered_bad_debt_inputs['was_evicted'] == False]

    return filtered_bad_debt_inputs, selected_month_year
    

def late_collections_over_ar(bad_debt_inputs, selected_month_year):
    st.subheader("Late Collections over BOM AR")

    bad_debt_inputs = bad_debt_inputs[bad_debt_inputs['bom_rent_balance'] > 0]

    # Graph the past 12 months
    monthly_summary = bad_debt_inputs.groupby('month').agg({
        'late_rent_collections': 'sum',
        'bom_rent_balance': 'sum'
    }).reset_index()
    monthly_summary['late_collections_ratio'] = (
        monthly_summary['late_rent_collections'] / monthly_summary['bom_rent_balance']
    )
    chart = alt.Chart(monthly_summary).mark_line(point=True).encode(
        x=alt.X('month:T', axis=alt.Axis(format='%b %Y', title='Month', labelFlush=False)),
        y=alt.Y('late_collections_ratio:Q', title='Late Collections Ratio', 
        axis=alt.Axis(format='.1%')), 
        color=alt.value('#15b8a6'),
        tooltip=[
            alt.Tooltip('month:T', title='Month', format='%b %Y'),
            alt.Tooltip('late_rent_collections:Q', title='Late Collections', format='$,.0f'),
            alt.Tooltip('bom_rent_balance:Q', title='BOM AR', format='$,.0f'),
            alt.Tooltip('late_collections_ratio:Q', title='Late Collections Ratio', format='.1%')
        ]
    )
    st.altair_chart(chart, use_container_width=True)

    # Table for selected month
    bad_debt_inputs['late_collections_ratio'] = round(
        bad_debt_inputs['late_rent_collections'] / bad_debt_inputs['bom_rent_balance'], 2
    )
    display_df = bad_debt_inputs[[
        'display_month',
        'fund',
        'address',
        'bom_rent_balance',
        'late_rent_collections',
        'late_collections_ratio'
    ]]
    st.dataframe(display_df[display_df['display_month'] == selected_month_year].reset_index(drop=True), use_container_width=True)



def ar_over_gpr(bad_debt_inputs, selected_month_year):
    st.subheader("BOM AR over GPR")

    bad_debt_inputs = bad_debt_inputs[bad_debt_inputs['bom_rent_balance'] >= 0]

    # Graph the past 12 months
    monthly_summary = bad_debt_inputs.groupby('month').agg({
        'bom_rent_balance': 'sum',
        'gpr_this_month': 'sum'
    }).reset_index()
    monthly_summary['ar_over_gpr'] = (
        monthly_summary['bom_rent_balance'] / monthly_summary['gpr_this_month']
    )
    chart = alt.Chart(monthly_summary).mark_line(point=True).encode(
        x=alt.X('month:T', axis=alt.Axis(format='%b %Y', title='Month', labelFlush=False)),
        y=alt.Y('ar_over_gpr:Q', title='AR Over GPR',
        axis=alt.Axis(format='.1%')), 
        color=alt.value('#15b8a6')
    )
    st.altair_chart(chart, use_container_width=True)

    # Table for selected month
    bad_debt_inputs['ar_over_gpr'] = round(
        bad_debt_inputs['bom_rent_balance'] / bad_debt_inputs['gpr_this_month'], 2
    )
    display_df = bad_debt_inputs[[
        'display_month',
        'fund',
        'address',
        'bom_rent_balance',
        'gpr_this_month',
        'ar_over_gpr'
    ]]

    st.dataframe(display_df[display_df['display_month'] == selected_month_year].reset_index(drop=True), use_container_width=True)