import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
from glob import glob
import os

# Set page config
st.set_page_config(
    page_title="Mai Shan Yun Dashboard",
    layout="wide"
)

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select Analysis", ["Inventory Analysis", "Shipment Analysis", "Sales Analysis"])

# Load common data
@st.cache_data
def load_data():
    # Load ingredients data
    ingredients = pd.read_csv('Ingredient.csv')
    
    # Load monthly sales data
    monthly_data = []
    months = ['may', 'june', 'july', 'august', 'september', 'october']
    
    for month in months:
        file_path = f'csv_files/{month}.csv'
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            df['Month'] = month.capitalize()
            monthly_data.append(df)
    
    sales_data = pd.concat(monthly_data, ignore_index=True)
    
    # Load shipment data
    shipments = pd.read_csv('Shipment.csv')
    
    return ingredients, sales_data, shipments, months

# Load all data
ingredients, sales_data, shipments, months = load_data()

if page == "Inventory Analysis":
    st.title("Inventory Analysis Dashboard")
    
    # Merge ingredients with sales data
    merged = pd.merge(
        ingredients,
        sales_data,
        left_on='Item name',
        right_on='Item Name',
        how='right'
    )

    # Calculate ingredient usage
    ingredient_cols = [col for col in ingredients.columns if col != 'Item name']
    
    # Convert to numeric and handle missing values
    for col in ingredient_cols:
        merged[col] = pd.to_numeric(merged[col], errors='coerce').fillna(0)
    merged['Count'] = pd.to_numeric(merged['Count'], errors='coerce').fillna(0)
    
    # Calculate totals
    for col in ingredient_cols:
        merged[f'{col}_total'] = merged[col] * merged['Count']
    
    # Group by month
    monthly_usage = merged.groupby('Month')[
        [f'{col}_total' for col in ingredient_cols]
    ].sum()
    
    monthly_usage.columns = [col.replace('_total', '') for col in monthly_usage.columns]
    
    # Filters
    selected_month = st.sidebar.selectbox("Select Month", months)
    n_ingredients = st.sidebar.slider("Number of ingredients to show", 5, 15, 10)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"Top {n_ingredients} Used Ingredients - {selected_month.capitalize()}")
        month_data = monthly_usage.loc[selected_month.capitalize()]
        top_ingredients = month_data.sort_values(ascending=False).head(n_ingredients)
        
        fig1 = px.bar(
            x=top_ingredients.index,
            y=top_ingredients.values,
            labels={'x': 'Ingredient', 'y': 'Usage'},
            title=f"Top {n_ingredients} Ingredients by Usage"
        )
        st.plotly_chart(fig1)
    
    with col2:
        st.subheader(f"Least {n_ingredients} Used Ingredients - {selected_month.capitalize()}")
        bottom_ingredients = month_data.sort_values(ascending=True).head(n_ingredients)
        
        fig2 = px.bar(
            x=bottom_ingredients.index,
            y=bottom_ingredients.values,
            labels={'x': 'Ingredient', 'y': 'Usage'},
            title=f"Bottom {n_ingredients} Ingredients by Usage"
        )
        st.plotly_chart(fig2)

elif page == "Shipment Analysis":
    st.title("Shipment Analysis Dashboard")
    
    # Calculate monthly frequency
    def monthlyFreq(freqType):
        if pd.isna(freqType):
            return np.nan
        freqType = str(freqType).lower().strip()
        if freqType == "weekly":
            return 4
        elif freqType == "biweekly":
            return 2
        elif freqType == "monthly":
            return 1
        else:
            return np.nan
    
    # Process shipment data
    shipments['Number of shipments'] = pd.to_numeric(shipments['Number of shipments'], errors='coerce').fillna(0)
    shipments['Quantity per shipment'] = pd.to_numeric(shipments['Quantity per shipment'], errors='coerce').fillna(0)
    shipments['Shipments per Month'] = shipments['frequency'].apply(monthlyFreq) * shipments['Number of shipments']
    shipments['Monthly Quantity (g)'] = shipments['Quantity per shipment'] * shipments['Shipments per Month']
    
    # Convert lbs to grams
    lbs_mask = shipments['Unit of shipment'].str.lower().str.strip() == 'lbs'
    shipments.loc[lbs_mask, 'Monthly Quantity (g)'] = shipments.loc[lbs_mask, 'Monthly Quantity (g)'] * 453.59237
    
    # Calculate average monthly usage
    merged = pd.merge(ingredients, sales_data, left_on='Item name', right_on='Item Name', how='right')
    ingredient_cols = [col for col in ingredients.columns if col != 'Item name']
    
    # Calculate monthly usage
    for col in ingredient_cols:
        merged[col] = pd.to_numeric(merged[col], errors='coerce').fillna(0)
    merged['Count'] = pd.to_numeric(merged['Count'], errors='coerce').fillna(0)
    
    for col in ingredient_cols:
        merged[f'{col}_total'] = merged[col] * merged['Count']
    
    monthly_usage = merged.groupby('Month')[[f'{col}_total' for col in ingredient_cols]].sum()
    avg_monthly_usage = monthly_usage.mean(axis=0)
    
    # Map ingredient names
    ingredient_name_map = {
        'Beef': 'braised beef used (g)',
        'Chicken': 'Braised Chicken(g)',
        'Ramen': 'Ramen (count)',
        'Rice Noodles': 'Rice Noodles(g)',
        'Flour': 'flour (g)',
        'Rice': 'Rice(g)',
        'Green Onion': 'Green Onion',
        'White Onion': 'White onion',
        'Cilantro': 'Cilantro',
        'Egg': 'Egg(count)',
        'Peas + Carrot': 'Peas(g)',
        'Bokchoy': 'Boychoy(g)',
        'Chicken Wings': 'Chicken Wings (pcs)'
    }
    
    # Build comparison data
    comparisonData = []
    for idx, row in shipments.iterrows():
        ingredientName = row['Ingredient']
        monthlySupply = row['Monthly Quantity (g)']
        
        usageCol = ingredient_name_map.get(ingredientName)
        if usageCol and usageCol in avg_monthly_usage.index:
            avgUsage = avg_monthly_usage[usageCol]
        else:
            avgUsage = 0
        
        if avgUsage > 0:
            utilization = (avgUsage / monthlySupply) * 100 if monthlySupply > 0 else 0
            daysOfSupply = (monthlySupply / (avgUsage / 30)) if avgUsage > 0 else 999
        else:
            utilization = 0
            daysOfSupply = 999
        
        comparisonData.append({
            'Ingredient': ingredientName,
            'monthlySupply': monthlySupply,
            'Avg_Monthly_Usage': avgUsage,
            'Difference': monthlySupply - avgUsage,
            'Utilization_%': utilization,
            'daysOfSupply': daysOfSupply
        })
    
    comparison = pd.DataFrame(comparisonData)
    
    # Create tabs for different analyses
    tab1, tab2, tab3 = st.tabs(["Monthly Supply", "Supply Gap", "Utilization Rate"])
    
    with tab1:
        st.subheader("Monthly Supply by Ingredient")
        shipments_sorted = shipments.sort_values('Monthly Quantity (g)', ascending=True)
        fig = px.bar(
            shipments_sorted,
            y='Ingredient',
            x='Monthly Quantity (g)',
            title='Estimated Monthly Supply per Ingredient',
            color_continuous_scale='viridis'
        )
        fig.update_layout(
            title_font=dict(size=16, weight='bold'),
            xaxis_title_font=dict(size=12),
            yaxis_title_font=dict(size=12)
        )
        st.plotly_chart(fig, width='stretch')
    
    with tab2:
        st.subheader("Supply Gap Analysis")
        comparison_sorted = comparison.sort_values('Difference', ascending=True)
        colors = ['red' if x < 0 else 'green' for x in comparison_sorted['Difference']]
        fig = px.bar(
            comparison_sorted,
            y='Ingredient',
            x='Difference',
            title='Supply Gap Analysis (Negative = Shortage Risk)',
            color='Difference',
            color_continuous_scale=['red', 'green'],
        )
        fig.add_vline(x=0, line_dash="dash", line_color="black", line_width=2)
        fig.update_layout(
            title_font=dict(size=16, weight='bold'),
            xaxis_title_font=dict(size=12),
            yaxis_title_font=dict(size=12)
        )
        st.plotly_chart(fig, width='stretch')
    
    # Calculate average monthly usage
    merged = pd.merge(
        ingredients,
        sales_data,
        left_on='Item name',
        right_on='Item Name',
        how='right'
    )
    
    # Calculate ingredient usage
    ingredient_cols = [col for col in ingredients.columns if col != 'Item name']
    for col in ingredient_cols:
        merged[col] = pd.to_numeric(merged[col], errors='coerce').fillna(0)
    merged['Count'] = pd.to_numeric(merged['Count'], errors='coerce').fillna(0)
    
    # Calculate monthly usage
    for col in ingredient_cols:
        merged[f'{col}_total'] = merged[col] * merged['Count']
    
    # Calculate average monthly usage per ingredient
    monthly_usage = merged.groupby('Month')[[f'{col}_total' for col in ingredient_cols]].sum()
    avg_monthly_usage = monthly_usage.mean(axis=0)
    
    # Calculate supply status
    def calculate_status(supply, usage):
        if usage == 0:
            return 'NO USAGE'
        days_of_supply = (supply / (usage / 30)) if usage > 0 else 999
        if days_of_supply < 5:
            return 'CRITICAL'
        elif days_of_supply < 10:
            return 'LOW'
        elif days_of_supply < 45:
            return 'GOOD'
        else:
            return 'OVERSTOCKED'
    
    # Map ingredient names
    ingredient_name_map = {
        'Beef': 'braised beef used (g)',
        'Chicken': 'Braised Chicken(g)',
        'Ramen': 'Ramen (count)',
        'Rice Noodles': 'Rice Noodles(g)',
        'Flour': 'flour (g)',
        'Rice': 'Rice(g)',
        'Green Onion': 'Green Onion',
        'White Onion': 'White onion',
        'Cilantro': 'Cilantro',
        'Egg': 'Egg(count)',
        'Peas + Carrot': 'Peas(g)',
        'Bokchoy': 'Boychoy(g)',
        'Chicken Wings': 'Chicken Wings (pcs)'
    }
    
    # Calculate status for each ingredient
    status_list = []
    for idx, row in shipments.iterrows():
        ingredient_name = row['Ingredient']
        monthly_supply = row['Monthly Quantity (g)']
        
        usage_col = ingredient_name_map.get(ingredient_name)
        if usage_col and usage_col in avg_monthly_usage.index:
            avg_usage = avg_monthly_usage[usage_col]
        else:
            avg_usage = 0
        
        status = calculate_status(monthly_supply, avg_usage)
        status_list.append(status)
    
    shipments['Status'] = status_list
    
    with tab3:
        st.subheader("Utilization Rate")
        comparison_sorted = comparison.sort_values('Utilization_%', ascending=False)
        
        # Create color scale similar to the original
        colors = ['red' if x > 90 else 'orange' if x > 50 else 'green' for x in comparison_sorted['Utilization_%']]
        
        fig = px.bar(
            comparison_sorted,
            y='Ingredient',
            x='Utilization_%',
            title='Ingredient Utilization Rate',
            color='Utilization_%',
            color_continuous_scale=['green', 'orange', 'red']
        )
        
        fig.add_vline(x=100, line_dash="dash", line_color="red", line_width=2)
        fig.update_layout(
            title_font=dict(size=16, weight='bold'),
            xaxis_title_font=dict(size=12),
            yaxis_title_font=dict(size=12)
        )
        st.plotly_chart(fig, width='stretch')
        status_data = pd.DataFrame(shipments['Status'].value_counts()).reset_index()
        status_data.columns = ['Status', 'Count']
        
        # Create a pie chart for status distribution
        fig = px.pie(
            status_data,
            values='Count',
            names='Status',
            title='Ingredient Supply Status Distribution',
            color='Status',
            color_discrete_map={
                'CRITICAL': 'red',
                'LOW': 'orange',
                'GOOD': 'green',
                'OVERSTOCKED': 'blue',
                'NO USAGE': 'gray'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Critical Items", len(shipments[shipments['Status'] == 'CRITICAL']))
        with col2:
            st.metric("Low Stock", len(shipments[shipments['Status'] == 'LOW']))
        with col3:
            st.metric("Good Stock", len(shipments[shipments['Status'] == 'GOOD']))
        with col4:
            st.metric("Overstocked", len(shipments[shipments['Status'] == 'OVERSTOCKED']))
        
        # Display detailed status table
        st.subheader("Detailed Status by Ingredient")
        status_table = shipments[['Ingredient', 'Monthly Quantity (g)', 'Status']]
        st.dataframe(status_table, use_container_width=True)

elif page == "Sales Analysis":
    st.title("Sales Analysis Dashboard")
    
    # Load and process monthly data exactly as in items_most_bought.py
    may = pd.read_csv('csv_files/may.csv')
    jun = pd.read_csv('csv_files/june.csv')
    jul = pd.read_csv('csv_files/july.csv')
    aug = pd.read_csv('csv_files/august.csv')
    sep = pd.read_csv('csv_files/september.csv')
    oct = pd.read_csv('csv_files/october.csv')
    
    # Drop unnecessary columns
    for df in [may, jun, jul, aug, sep, oct]:
        df.drop(['source_page', 'source_table'], axis=1, inplace=True)
    
    # Combine all months
    months_df = pd.concat([may, jun, jul, aug, sep, oct], axis=0)
    months_df['Count'] = months_df['Count'].replace(',', '', regex=True).astype(float)
    months_df['Amount'] = months_df['Amount'].replace(',', '', regex=True).astype(float)
    months_df['Item Name'] = months_df['Item Name'].replace(' ', '\n', regex=True)
    
    # Create summary dataframes
    summary_amount_df = (
        months_df
        .groupby('Item Name', as_index=False)
        .agg({'Count': 'sum', 'Amount': 'sum'})
        .sort_values('Amount', ascending=False)
    )
    
    summary_count_df = summary_amount_df.copy()
    summary_count_df = summary_count_df[summary_count_df['Amount'] != 0]
    
    # Get top 20
    t20_spending = summary_amount_df.head(20)
    t20_count = summary_count_df.sort_values('Count', ascending=False).head(20)
    
    tab1, tab2 = st.tabs(["Revenue Analysis", "Sales Count Analysis"])
    
    with tab1:
        st.subheader("All Time Spending for Top 20 Items")
        fig = px.bar(
            t20_spending,
            y='Amount',
            x='Item Name',
            title='All Time Spending for Top 20 Items',
            labels={'Amount': 'Total Spending ($)', 'Item Name': 'Item Name'},
            color_discrete_sequence=['orange'] * len(t20_spending)
        )
        fig.update_layout(
            xaxis_tickangle=45,
            title_font=dict(size=16, weight='bold'),
            xaxis_title_font=dict(size=12, weight='bold'),
            yaxis_title_font=dict(size=12, weight='bold')
        )
        st.plotly_chart(fig, width='stretch')
    
    with tab2:
        st.subheader("All Time Count Sold for Top 20 Items")
        fig = px.bar(
            t20_count,
            y='Count',
            x='Item Name',
            title='All Time Count Sold for Top 20 Items',
            labels={'Count': 'Total Count', 'Item Name': 'Item Name'},
            color_discrete_sequence=['purple'] * len(t20_count)
        )
        fig.update_layout(
            xaxis_tickangle=45,
            title_font=dict(size=16, weight='bold'),
            xaxis_title_font=dict(size=12, weight='bold'),
            yaxis_title_font=dict(size=12, weight='bold')
        )
        st.plotly_chart(fig, width='stretch')