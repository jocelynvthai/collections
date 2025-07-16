import streamlit as st
import altair as alt
from datetime import datetime

from tabs.utils import date_month_filter, fund_filter, color_scale, dash_scale

def late_collections_curve_filters(collections_curve_data):
    # Make the fund filter column wider than the others
    col_month, col_bom_rent_balance, col_num_rentals, col_num_rentals_in_evictions, _, col_fund_filter = st.columns([1, 1, 1, 1, 1, 1])
    with col_fund_filter:
        selected_fund = fund_filter(key='late_collections_curve_select_fund', data=collections_curve_data)

    datapoint = collections_curve_data[collections_curve_data['fund'] == selected_fund].iloc[-1]
    with col_month:
        st.metric(f"{datetime.now().strftime('%Y')}", f"{datetime.now().strftime('%B')}")
    with col_bom_rent_balance:
        st.metric("BOM AR", f"${datapoint['bom_rent_balance_this_month']:,.0f}")
    with col_num_rentals:
        st.metric("Homes with BOM AR", f"{datapoint['homes_with_bom_rent_balance_this_month']:,}")
    with col_num_rentals_in_evictions:
        st.metric("Homes in Evictions With BOM AR", f"{datapoint['homes_with_bom_rent_balance_in_evictions_this_month']:,}")
    return selected_fund


def late_collections_curve(collections_curve_data, selected_fund):
    st.subheader("Late Collections Curve")

    display_df = collections_curve_data[collections_curve_data['fund'] == selected_fund].copy()

    # Melt to long format for Altair
    chart_df = display_df.melt(
        id_vars=['day_of_month', 'rent_paid_late_this_month', 'rent_succeeded_late_this_month'],
        value_vars=[
            'late_collections_rate_succeeded_this_month',
            'late_collections_rate_this_month',
            'late_collections_rate_last_month',
            'late_collections_rate_l3m',
            'late_collections_rate_l12m'
        ],
        var_name='curve',
        value_name='ratio'
    )

    chart_df['curve'] = chart_df['curve'].map({
        'late_collections_rate_succeeded_this_month': 'This Month Succeeded',
        'late_collections_rate_this_month': 'This Month Paid',
        'late_collections_rate_last_month': 'Last Month',
        'late_collections_rate_l3m': 'Last 3 Months',
        'late_collections_rate_l12m': 'Last 12 Months'
    })
    chart_df = chart_df[(
        ((chart_df['curve'].isin(['This Month Succeeded', 'This Month Paid'])) & (chart_df['day_of_month'] <= datetime.today().day)) |
        (~chart_df['curve'].isin(['This Month Succeeded', 'This Month Paid']))
    )]

    chart = alt.Chart(chart_df).mark_line().encode(
        x=alt.X('day_of_month:O', title='Day of Month'),
        y=alt.Y(
            'ratio:Q',
            title='Collections Rate',
            axis=alt.Axis(format='%'),
            scale=alt.Scale(domain=[0, 1])
        ),
        color=alt.Color(
            'curve:N',
            title='Curve',
            scale=color_scale,
            legend=alt.Legend(orient='right')
        ),
        strokeDash=alt.StrokeDash('curve:N', scale=dash_scale),
        tooltip=['day_of_month', 'curve', alt.Tooltip('ratio:Q', format='.2%')]
    ).properties(
        width='container'
    ).interactive()

    # Add points only for "This Month Succeeded" and "This Month Paid"
    point_chart = alt.Chart(chart_df[chart_df['curve'].isin(['This Month Succeeded', 'This Month Paid'])]).mark_point(
        filled=True,
        size=60
    ).encode(
        x=alt.X('day_of_month:O'),
        y=alt.Y('ratio:Q'),
        color=alt.Color('curve:N', scale=color_scale, legend=None),
        tooltip=[
            'day_of_month', 
            'curve', 
            alt.Tooltip('ratio:Q', format='.2%'),
            alt.Tooltip('rent_paid_late_this_month:Q', format='$,.0f', title='Rent Paid Late'),
            alt.Tooltip('rent_succeeded_late_this_month:Q', format='$,.0f', title='Rent Succeeded Late')
        ]
    )
    
    st.altair_chart(chart + point_chart, use_container_width=True)

def late_collections_drilldown(bad_debt_inputs, selected_fund):
    st.subheader("Late Collections Drilldown")
    
    selected_month_year = date_month_filter(key='late_collections_select_month_year')

    display_df = bad_debt_inputs[(bad_debt_inputs['bom_rent_balance'] > 0)]
    display_df = display_df[(display_df['display_month'] == selected_month_year)]
    if selected_fund != 'All':
        display_df = display_df[display_df['fund'] == selected_fund]
    
    display_df['late_collections_ratio'] = display_df['late_rent_collections'] / display_df['bom_rent_balance']
    st.dataframe(display_df[['display_month', 'address', 'fund', 'bom_rent_balance', 'late_rent_collections', 'late_collections_ratio']].reset_index(drop=True), use_container_width=True)

