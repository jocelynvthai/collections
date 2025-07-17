import streamlit as st
import altair as alt
from datetime import datetime

from tabs.utils import date_month_filter, fund_filter, color_scale, dash_scale


def ontime_collections_curve_filters(collections_curve_data):
    selected_fund = fund_filter(key='ontime_collections_curve_select_fund', data=collections_curve_data)
    col_month, col_rent_charged, col_today_paid, col_today_succeeded, col_today_l1m, col_today_l3m, col_today_l12m = st.columns([1, 1, 1, 1, 1, 1, 1])

    datapoint = collections_curve_data[(collections_curve_data['fund'] == selected_fund) & (collections_curve_data['day_of_month'] == datetime.now().day)].iloc[0]
    with col_month:
        st.metric(f"{datetime.now().strftime('%Y')}", f"{datetime.now().strftime('%B %d')}")
    with col_rent_charged:
        st.metric("Rent Charged", f"${datapoint['rent_charged_this_month']:,.0f}")
    with col_today_paid:
        st.metric(f"Rent Paid", f"{datapoint['ontime_collections_rate_this_month'] * 100:.2f}%")
    with col_today_succeeded:
        st.metric(f"Rent Succeeded", f"{datapoint['ontime_collections_rate_succeeded_this_month'] * 100:.2f}%")
    with col_today_l1m:
        st.metric(f"Last Month Paid", f"{datapoint['ontime_collections_rate_last_month'] * 100:.2f}%")
    with col_today_l3m:
        st.metric(f"Last 3 Months Paid", f"{datapoint['ontime_collections_rate_l3m'] * 100:.2f}%")
    with col_today_l12m:
        st.metric(f"Last 12 Months Paid", f"{datapoint['ontime_collections_rate_l12m'] * 100:.2f}%")

    return selected_fund


    

def ontime_collections_curve(collections_curve_data, selected_fund):
    st.subheader("On-Time Collections Curve")

    chart_df = collections_curve_data[collections_curve_data['fund'] == selected_fund].copy()
    # Melt to long format for Altair
    chart_df = chart_df.melt(
        id_vars=['day_of_month', 'rent_charged_this_month', 'rent_paid_ontime_this_month', 'rent_succeeded_ontime_this_month', 'rent_processing_ontime_this_month'],  
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
        tooltip=[
            'day_of_month', 
            'curve', 
            alt.Tooltip('ratio:Q', format='.2%')
        ]
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
        tooltip=[
            'day_of_month', 
            'curve', 
            alt.Tooltip('ratio:Q', format='.2%'),
            alt.Tooltip('rent_paid_ontime_this_month:Q', format='$,.0f', title='Rent Paid On Time'),
            alt.Tooltip('rent_succeeded_ontime_this_month:Q', format='$,.0f', title='Rent Succeeded On Time'),
            alt.Tooltip('rent_processing_ontime_this_month:Q', format='$,.0f', title='Rent Processing On Time')
        ]
    )

    st.altair_chart(chart + point_chart, use_container_width=True)


def ontime_collections_drilldown(bad_debt_inputs, selected_fund):
    st.subheader("On-Time Collections Drilldown")
    
    selected_month_year = date_month_filter(key='ontime_collections_select_month_year')

    display_df = bad_debt_inputs[(bad_debt_inputs['rent_charged'] > 0)]
    display_df = display_df[(display_df['display_month'] == selected_month_year)]
    if selected_fund != 'All':
        display_df = display_df[display_df['fund'] == selected_fund]
    
    display_df['unpaid_rent_this_month'] = round(display_df['unpaid_rent_this_month'], 2)
    display_df['hudson_link'] = "https://hudson.upandup.co/rent-roll/" + display_df['rental_id'].astype(str)
    display_df['buildium_link'] = "https://upandup.managebuilding.com/manager/app/rentroll/" + display_df['buildium_lease_id'].astype(str) + "/financials/ledger?isByAccountView=0&isByDateView=1"
    
    st.dataframe(
        display_df[[
            'address', 
            'fund', 
            'in_evictions_this_month', 
            'rent_charged', 
            'ontime_rent_collections_succeeded', 
            'ontime_rent_collections_processing', 
            'unpaid_rent_this_month', 
            'hudson_link', 
            'buildium_link'
        ]].rename(columns={
            'address': 'Address',
            'fund': 'Fund',
            'in_evictions_this_month': 'In Evictions',
            'rent_charged': 'Rent Charged',
            'ontime_rent_collections_succeeded': 'On-Time Collections (Succeeded)',
            'ontime_rent_collections_processing': 'On-Time Collections (Processing)',
            'unpaid_rent_this_month': 'Unpaid Rent', 
        }).sort_values(by='Unpaid Rent', ascending=False).reset_index(drop=True),
        use_container_width=True,
        column_config={
            "hudson_link": st.column_config.LinkColumn(
                "Hudson Link", 
                display_text="Hudson",
                width="small"
            ), 
            "buildium_link": st.column_config.LinkColumn(
                "Buildium Link", 
                display_text="Buildium",
                width="small"
            )
        }
    )



