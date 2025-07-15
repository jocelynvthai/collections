import streamlit as st
import altair as alt
from datetime import datetime

from tabs.utils import date_month_filter, fund_filter, color_scale, dash_scale


def ontime_collections_curve_filters(collections_curve_data):
    selected_fund = fund_filter(key='ontime_collections_curve_select_fund', data=collections_curve_data)
    return selected_fund
    

def ontime_collections_curve(collections_curve_data, selected_fund):
    st.subheader("On-Time Collections Curve")

    display_df = collections_curve_data[collections_curve_data['fund'] == selected_fund].copy()

    # Melt to long format for Altair
    chart_df = display_df.melt(
        id_vars=['day_of_month'],
        value_vars=[
            'ontime_collections_rate_succeeded_this_month',
            'ontime_collections_rate_this_month',
            'ontime_collections_rate_last_month',
            'ontime_collections_rate_l3m',
            'ontime_collections_rate_l12m'
        ],
        var_name='curve',
        value_name='ratio'
    )

    chart_df['curve'] = chart_df['curve'].map({
        'ontime_collections_rate_succeeded_this_month': 'This Month Succeeded',
        'ontime_collections_rate_this_month': 'This Month Paid',
        'ontime_collections_rate_last_month': 'Last Month',
        'ontime_collections_rate_l3m': 'Last 3 Months',
        'ontime_collections_rate_l12m': 'Last 12 Months'
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
            scale=alt.Scale(domain=[0.5, 1])
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
        width='container',
        height=400
    ).interactive()

    # Add points only for "This Month Succeeded" and "This Month Paid"
    point_chart = alt.Chart(chart_df[chart_df['curve'].isin(['This Month Succeeded', 'This Month Paid'])]).mark_point(
        filled=True,
        size=60
    ).encode(
        x=alt.X('day_of_month:O'),
        y=alt.Y('ratio:Q'),
        color=alt.Color('curve:N', scale=color_scale, legend=None),
        tooltip=['day_of_month', 'curve', alt.Tooltip('ratio:Q', format='.2%')]
    )

    st.altair_chart(chart + point_chart, use_container_width=True)


def ontime_collections_drilldown(bad_debt_inputs, selected_fund):
    st.subheader("On-Time Collections Drilldown")
    
    selected_month_year = date_month_filter(key='ontime_collections_select_month_year')

    display_df = bad_debt_inputs[(bad_debt_inputs['rent_charged'] > 0)]
    display_df = display_df[(display_df['display_month'] == selected_month_year)]
    if selected_fund != 'All':
        display_df = display_df[display_df['fund'] == selected_fund]
    
    display_df['ontime_collections_ratio'] = display_df['ontime_rent_collections'] / display_df['rent_charged']
    st.dataframe(display_df[['display_month', 'address', 'fund', 'rent_charged', 'ontime_rent_collections', 'ontime_collections_ratio']].reset_index(drop=True), use_container_width=True)



