import streamlit as st
import altair as alt
from datetime import datetime

from tabs.utils import date_month_filter, fund_filter, color_scale, dash_scale

def late_collections_curve_filters(collections_curve_data):
    selected_fund = fund_filter(key='late_collections_curve_select_fund', data=collections_curve_data)
    col_month, col_num_rentals, col_num_rentals_in_evictions, col_bom_rent_balance, col_today_paid, col_today_succeeded, col_today_l1m, col_today_l3m, col_today_l12m = st.columns([.75, .75, .75, 1, 1, 1, 1, 1, 1])

    datapoint = collections_curve_data[(collections_curve_data['fund'] == selected_fund) & (collections_curve_data['day_of_month'] == datetime.now().day)].iloc[0]
    with col_month:
        st.metric(f"{datetime.now().strftime('%Y')}", f"{datetime.now().strftime('%B')}")
    with col_bom_rent_balance:
        st.metric("BOM AR", f"${datapoint['bom_rent_balance_this_month']:,.0f}")
    with col_num_rentals:
        st.metric("🏠", f"{datapoint['homes_with_bom_rent_balance_this_month']:,}")
    with col_num_rentals_in_evictions:
        st.metric("🏠 in Evictions", f"{datapoint['homes_with_bom_rent_balance_in_evictions_this_month']:,}")
    with col_today_paid:
        st.metric("Rent Paid", f"{datapoint['late_collections_rate_this_month'] * 100:.2f}%")
    with col_today_succeeded:
        st.metric("Rent Succeeded", f"{datapoint['late_collections_rate_succeeded_this_month'] * 100:.2f}%")
    with col_today_l1m:
        st.metric("Last Month Paid", f"{datapoint['late_collections_rate_last_month'] * 100:.2f}%")
    with col_today_l3m:
        st.metric("Last 3 Months Paid", f"{datapoint['late_collections_rate_l3m'] * 100:.2f}%")
    with col_today_l12m:
        st.metric("Last 12 Months Paid", f"{datapoint['late_collections_rate_l12m'] * 100:.2f}%")

    return selected_fund


def late_collections_curve(collections_curve_data, selected_fund):
    st.subheader("Late Collections Curve")

    chart_df = collections_curve_data[collections_curve_data['fund'] == selected_fund].copy()

    # Melt to long format for Altair
    chart_df = chart_df.melt(
        id_vars=['day_of_month', 'rent_paid_late_this_month', 'rent_succeeded_late_this_month', 'rent_processing_late_this_month'],
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
            axis=alt.Axis(format='%')
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
            alt.Tooltip('rent_succeeded_late_this_month:Q', format='$,.0f', title='Rent Succeeded Late'), 
            alt.Tooltip('rent_processing_late_this_month:Q', format='$,.0f', title='Rent Processing Late')
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
    
    display_df['unpaid_late_rent_this_month'] = round(display_df['bom_rent_balance'] - display_df['late_rent_collections_succeeded'] - display_df['late_rent_collections_processing'], 2)
    display_df['hudson_link'] = "https://hudson.upandup.co/rent-roll/" + display_df['rental_id'].astype(str)
    
    st.dataframe(
        display_df[['address', 'fund', 'eviction_status', 'bom_rent_balance', 'late_rent_collections_succeeded', 'late_rent_collections_processing', 'unpaid_late_rent_this_month', 'hudson_link']].sort_values(by='unpaid_late_rent_this_month', ascending=False).reset_index(drop=True),
        use_container_width=True,
        column_config={
            "hudson_link": st.column_config.LinkColumn(
                "Hudson Link", 
                display_text="Hudson",
                width="small"
            )
        }
    )

