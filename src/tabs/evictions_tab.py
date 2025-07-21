import streamlit as st

from tabs.utils import fund_filter 

def evictions(evictions_data):
    selected_fund = fund_filter(key='evictions_select_fund', data=evictions_data, include_all=True)
    
    if selected_fund != 'All':
        fund_evictions_data = evictions_data[evictions_data['fund'] == selected_fund]
    else:
        fund_evictions_data = evictions_data.copy()

    for status in ['pending', 'completed', 'canceled']:
        st.subheader(f"{status.title()} Evictions")

        display_df = fund_evictions_data[fund_evictions_data['status'] == status]
        display_df['rental_link'] = "https://hudson.upandup.co/rent-roll/" + display_df['rental_id'].astype(str)
            
        display_df = display_df[[ 
            'rental_link', 
            'address',
            'fund', 
            'status', 
            'created_at', 
            'updated_at', 
            'canceled_at', 
            'canceled_by_admin_name', 
            'cancelation_reason', 
            'completed_at', 
            'completed_by_admin_name', 
            'file_sent_to_attorney_at', 
            'file_sent_to_attorney_by_admin_name', 
            'filed_at', 
            'filed_by_admin_name', 
            'court_date', 
            'writ_date', 
            'projected_possession_date', 
            'set_out_date',
            'notes'
        ]].rename(columns={
            'address': 'Address',
            'fund': 'Fund',
            'status': 'Status',
            'created_at': 'Created At',
            'updated_at': 'Updated At',
            'canceled_at': 'Canceled At',
            'canceled_by_admin_name': 'Canceled By',
            'cancelation_reason': 'Cancelation Reason',
            'completed_at': 'Completed At',
            'completed_by_admin_name': 'Completed By',
            'file_sent_to_attorney_at': 'Sent to Attorney At',
            'file_sent_to_attorney_by_admin_name': 'Sent to Attorney By',
            'filed_at': 'Filed At',
            'filed_by_admin_name': 'Filed By',
            'court_date': 'Court Date',
            'writ_date': 'Writ Date',
            'projected_possession_date': 'Projected Possession Date',
            'set_out_date': 'Set Out Date', 
            'notes': 'Notes'
        })

        
        datetime_columns = [col for col in display_df.columns if col.endswith(' At')]
        for col in datetime_columns:
            display_df[col] = display_df[col].dt.strftime('%Y-%m-%d %I:%M%p')

        def color_status(val):
            colors = {
                'pending': 'color: #FF9966', 
                'completed': 'color: #E77C8E',
                'canceled': 'color: #A9A9A9' 
            }
            return colors.get(val.lower(), '')
        styled_df = display_df.sort_values(by='Updated At', ascending=False).reset_index(drop=True).style.applymap(color_status, subset=['Status'])
        st.dataframe(styled_df, 
                     column_config={
                        'rental_link': st.column_config.LinkColumn(
                            label='Rental', 
                            display_text=":material/link:",
                            width="small"
                        )
                     })

        