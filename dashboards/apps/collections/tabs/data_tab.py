import streamlit as st
import altair as alt

from tabs.utils import date_month_filter, fund_filter


def data_filters(bad_debt_inputs_data):
    fund, rental_status, eviction_status, month_year, bom_ar = st.columns([2, 1.5, 1.5, 1.5, 1])
    with fund:
        selected_fund = fund_filter(key='data_select_fund', data=bad_debt_inputs_data, include_all=True)
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
    with month_year:
        selected_month_year = date_month_filter(key='data_select_month_year')
    
    filtered_bad_debt_inputs = bad_debt_inputs_data.copy()
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
    
    with bom_ar:
        st.metric(f"BOM AR ({selected_month_year})", f"${filtered_bad_debt_inputs[filtered_bad_debt_inputs['display_month'] == selected_month_year]['bom_rent_balance'].sum():,.0f}")

    return filtered_bad_debt_inputs, selected_month_year
    

def late_collections_over_ar(bad_debt_inputs_data, selected_month_year):
    st.subheader("Late Collections over BOM AR")

    bad_debt_inputs_data = bad_debt_inputs_data[bad_debt_inputs_data['bom_rent_balance'] > 0]
    bad_debt_inputs_data['total_late_rent_collections'] = bad_debt_inputs_data['late_rent_collections_succeeded'] + bad_debt_inputs_data['late_rent_collections_processing']

    # Graph the past 12 months
    monthly_summary = bad_debt_inputs_data.groupby('month').agg({
        'total_late_rent_collections': 'sum',
        'bom_rent_balance': 'sum'
    }).reset_index()
    monthly_summary['late_collections_ratio'] = (
        monthly_summary['total_late_rent_collections']/ monthly_summary['bom_rent_balance']
    )
    chart = alt.Chart(monthly_summary).mark_line(point=True).encode(
        x=alt.X('month:T', axis=alt.Axis(format='%b %Y', title='Month', labelFlush=False)),
        y=alt.Y('late_collections_ratio:Q', title='Late Collections Ratio', 
        axis=alt.Axis(format='.1%')), 
        color=alt.value('#15b8a6'),
        tooltip=[
            alt.Tooltip('month:T', title='Month', format='%b %Y'),
            alt.Tooltip('total_late_rent_collections:Q', title='Late Collections', format='$,.0f'),
            alt.Tooltip('bom_rent_balance:Q', title='BOM AR', format='$,.0f'),
            alt.Tooltip('late_collections_ratio:Q', title='Late Collections Ratio', format='.1%')
        ]
    )
    st.altair_chart(chart)

    # Table for selected month
    bad_debt_inputs_data['late_collections_ratio'] = round(
        bad_debt_inputs_data['total_late_rent_collections'] / bad_debt_inputs_data['bom_rent_balance'], 2
    )
    display_df = bad_debt_inputs_data[bad_debt_inputs_data['display_month'] == selected_month_year].sort_values(by='total_late_rent_collections', ascending=False).reset_index(drop=True)
    st.dataframe(display_df[[
        'fund',
        'address',
        'bom_rent_balance',
        'late_rent_collections_succeeded',
        'late_rent_collections_processing',
        'total_late_rent_collections',
        'late_collections_ratio'
    ]].rename(columns={
        'fund': 'Fund',
        'address': 'Address',
        'bom_rent_balance': 'BOM AR',
        'late_rent_collections_succeeded': 'Late Collections (Succeeded)',
        'late_rent_collections_processing': 'Late Collections (Processing)',
        'total_late_rent_collections': 'Late Collections (Total)',
        'late_collections_ratio': 'Late Collections (Total)/BOM AR'
    }))



def ar_over_gpr(bad_debt_inputs_data, selected_month_year):
    st.subheader("BOM AR over GPR")

    bad_debt_inputs_data = bad_debt_inputs_data[bad_debt_inputs_data['bom_rent_balance'] >= 0]

    # Graph the past 12 months
    monthly_summary = bad_debt_inputs_data.groupby('month').agg({
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
    st.altair_chart(chart)

     # Table for selected month
    bad_debt_inputs_data['ar_over_gpr'] = round(
        bad_debt_inputs_data['bom_rent_balance'] / bad_debt_inputs_data['gpr_this_month'], 2
    )
    display_df = bad_debt_inputs_data[(bad_debt_inputs_data['display_month'] == selected_month_year) & (bad_debt_inputs_data['bom_rent_balance'] > 0)].sort_values(by='bom_rent_balance', ascending=False).reset_index(drop=True)
    st.dataframe(display_df[[
        'fund',
        'address',
        'bom_rent_balance',
        'gpr_this_month',
        'ar_over_gpr'
    ]].rename(columns={
        'fund': 'Fund',
        'address': 'Address',
        'bom_rent_balance': 'BOM AR',
        'gpr_this_month': 'GPR',
        'ar_over_gpr': 'BOM AR/GPR'
    }))
