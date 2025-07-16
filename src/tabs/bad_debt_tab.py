import streamlit as st
import altair as alt
import numpy as np
import pandas as pd
from datetime import datetime

def bad_debt_over_time_filters(bad_debt_inputs):
    selected_fund = st.selectbox("Select Fund", bad_debt_inputs['fund'].unique())
    return selected_fund

def bad_debt_over_time(bad_debt_inputs, selected_fund):
    st.subheader("Bad Debt Over Time")

    bad_debt = bad_debt_inputs[bad_debt_inputs['fund'] == selected_fund].copy()
    # Calculate bad_debt as a new column, element-wise
    bad_debt['bad_debt'] = np.maximum(
        bad_debt['unpaid_rent_this_month']
        - bad_debt['unpaid_rent_covered_by_wallet']
        - bad_debt['bom_bad_debt_recovered_by_late_collections'], 0
    )

    # Group by fund and month, aggregate sums
    bad_debt_fund = (
        bad_debt.groupby(['fund', 'month'])
        .agg({'bad_debt': 'sum', 'rent_charged': 'sum'})
        .reset_index()
    )

    # Calculate the ratio
    bad_debt_fund['bad_debt_ratio_percent'] = bad_debt_fund['bad_debt'] * 100 / bad_debt_fund['rent_charged']

    # Set 'month' to the 15th of each month for centering
    bad_debt_fund['month'] = (
        pd.to_datetime(bad_debt_fund['month'])
        .dt.to_period('M')
        .dt.to_timestamp()
        + pd.Timedelta(days=7)
    )


    # Create a list of months for the domain (15th of each month)
    all_months = pd.date_range(
        start=(bad_debt_fund['month'].min() - pd.DateOffset(months=1)).replace(day=15),
        end=bad_debt_fund['month'].max(),
        freq='MS'
    ) + pd.Timedelta(days=1)

    chart = alt.Chart(bad_debt_fund).mark_bar(size=40, color='#26a69a').encode(
        x=alt.X(
            'month:T',
            title='Month',
            axis=alt.Axis(
                format='%b %Y',
                labelAngle=0,
                tickCount='month',
                labelPadding=15,
                labelAlign='left'
            ),
            scale=alt.Scale(domain=list(all_months))
        ),
        y=alt.Y('bad_debt_ratio_percent:Q', title='Bad Debt Ratio (%)'),
        tooltip=[
            alt.Tooltip('month:T', title='Month', format='%b %Y'),
            alt.Tooltip('bad_debt:Q', title='Bad Debt', format=','),
            alt.Tooltip('rent_charged:Q', title='Rent Charged', format=','),
            alt.Tooltip('bad_debt_ratio_percent:Q', title='Bad Debt Ratio (%)', format='.2f'),
        ]
    ).properties(
        title=f'Bad Debt Ratio for Fund: {selected_fund}',
        width=600
    )

    st.altair_chart(chart, use_container_width=True)


def bad_debt_projection(bad_debt_inputs, selected_fund):
    st.subheader("Bad Debt Projection")
    bad_debt_fund_inputs = bad_debt_inputs[(bad_debt_inputs['fund'] == selected_fund) & (bad_debt_inputs['month'] == datetime.now().strftime('%Y-%m-01'))]

    today_ocr = bad_debt_fund_inputs['ontime_rent_collections'].sum() / bad_debt_fund_inputs['rent_charged'].sum()
    today_lcr = 0 if bad_debt_fund_inputs['bom_rent_balance'].sum() == 0 else bad_debt_fund_inputs['late_rent_collections'].sum() / bad_debt_fund_inputs['bom_rent_balance'].sum()

    # New bad debt with OCR slider
    col_new, col_ocr = st.columns([0.5, 1])
    with col_ocr:
        selected_ocr = st.slider("Expected Ontime Collections Rate (OCR) %", min_value=0, max_value=100, value=96, step=1)
        expected_ocr = selected_ocr/100

    # Old bad debt recovery with LCR slider
    col_old, col_lcr = st.columns([0.5, 1])
    with col_lcr:
        selected_lcr = st.slider(
            "Expected Late Collections Rate (LCR) %",
            min_value=int(today_lcr * 100), 
            max_value=100,
            value=max(25, int(today_lcr * 100)),
            step=1, 
            help=f'Minimum value is set to current month\'s LCR: {today_lcr:.1%}'
        )
        expected_lcr = selected_lcr/100
        

    # Calculate all projections
    total_expected_bad_debt_increase = 0
    unpaid_rentals = bad_debt_fund_inputs[bad_debt_fund_inputs['ontime_rent_collections'] < bad_debt_fund_inputs['rent_charged']]
    for _, ur in unpaid_rentals.iterrows(): 
        amount_unpaid = ur['rent_charged'] - ur['ontime_rent_collections']
        expected_collections_pct = (expected_ocr - today_ocr) / (1 - today_ocr)
        expected_unpaid = amount_unpaid * (1 - expected_collections_pct)
        expected_bad_debt_increase = max(0, expected_unpaid - ur['bom_usable_wallet_or_deposit'])
        total_expected_bad_debt_increase += expected_bad_debt_increase

    total_expected_bad_debt_decrease = 0
    late_rentals = bad_debt_fund_inputs[bad_debt_fund_inputs['bom_rent_balance'] > 0]
    for _, lr in late_rentals.iterrows():	
        remaining_bom_balance = lr['bom_rent_balance'] - lr['late_rent_collections']
        expected_collections_pct = (expected_lcr - today_lcr) / (1 - today_lcr)
        expected_late_collections = remaining_bom_balance * expected_collections_pct
        expected_bad_debt_decrease = min(lr['bom_bad_debt_rent'], expected_late_collections)
        total_expected_bad_debt_decrease += expected_bad_debt_decrease

    fund_bad_debt_projection = total_expected_bad_debt_increase - total_expected_bad_debt_decrease

    # Calculate percentages of rent charged
    total_rent_charged = bad_debt_fund_inputs['rent_charged'].sum()
    new_bad_debt_pct = (total_expected_bad_debt_increase / total_rent_charged) * 100
    recovery_pct = (total_expected_bad_debt_decrease / total_rent_charged) * 100
    net_projection_pct = (fund_bad_debt_projection / total_rent_charged) * 100

    # Display metrics in order
    # 1. Net projection at the top
    st.metric(
        label=f"Net Bad Debt Projection ({datetime.now().strftime('%B %Y')})",
        value=f"{net_projection_pct:.2f}%",
        help="""The overall expected bad debt position as a percentage of rent charged. \n
- A negative percentage indicates net recovery (good) 
- A positive percentage indicates net increase in bad debt (bad)"""
    )

    # 2. New bad debt metric
    with col_new:
        st.metric(
            label="Projected New Bad Debt",
            value=f"{new_bad_debt_pct:.2f}%",
            help="""Represents potential new bad debt as a percentage of rent charged.  \n
Calculated after considering:
- Current month's collection progress
- Expected additional on-time collections based on OCR target
- Available wallet/deposit amounts that can offset unpaid rent"""
        )

    # 3. Old bad debt recovery metric
    with col_old:
        st.metric(
            label="Projected Old Bad Debt Recovery",
            value=f"{recovery_pct:.2f}%",
            help="""Amount of existing bad debt we expect to recover as a percentage of rent charged. \n
Based on:
- Current late collection progress
- Expected additional late collections based on LCR target
- Bad debt balance from beginning of month"""
        )





