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
    shipments['Shipments per Month'] = shipments['frequency'].apply(monthlyFreq) * shipments['Number of shipments']
    shipments['Monthly Quantity (g)'] = shipments['Quantity per shipment'] * shipments['Shipments per Month']
    
    # Convert lbs to grams
    lbs_mask = shipments['Unit of shipment'].str.lower().str.strip() == 'lbs'
    shipments.loc[lbs_mask, 'Monthly Quantity (g)'] = shipments.loc[lbs_mask, 'Monthly Quantity (g)'] * 453.59237
    
    # Create tabs for different analyses
    tab1, tab2, tab3 = st.tabs(["Supply Analysis", "Usage Trends", "Insights"])
    
    with tab1:
        st.subheader("Monthly Supply by Ingredient")
        fig = px.bar(
            shipments.sort_values('Monthly Quantity (g)', ascending=True),
            y='Ingredient',
            x='Monthly Quantity (g)',
            title='Estimated Monthly Supply per Ingredient'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Shipment Frequency Distribution")
        freq_data = shipments['frequency'].value_counts()
        fig = px.pie(
            values=freq_data.values,
            names=freq_data.index,
            title='Distribution of Shipment Frequencies'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("Supply Status")
        status_data = shipments['Status'].value_counts()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Critical Items", len(shipments[shipments['Status'] == 'CRITICAL']))
        with col2:
            st.metric("Low Stock", len(shipments[shipments['Status'] == 'LOW']))
        with col3:
            st.metric("Good Stock", len(shipments[shipments['Status'] == 'GOOD']))
        with col4:
            st.metric("Overstocked", len(shipments[shipments['Status'] == 'OVERSTOCKED']))

elif page == "Sales Analysis":
    st.title("Sales Analysis Dashboard")
    
    # Clean and prepare sales data
    sales_data['Count'] = pd.to_numeric(sales_data['Count'].replace(',', '', regex=True))
    sales_data['Amount'] = pd.to_numeric(sales_data['Amount'].astype(str).str.replace(',', ''))
    
    # Create summary dataframes
    summary_amount = (
        sales_data
        .groupby('Item Name')
        .agg({'Count': 'sum', 'Amount': 'sum'})
        .sort_values('Amount', ascending=False)
    )
    
    tab1, tab2 = st.tabs(["Revenue Analysis", "Sales Count Analysis"])
    
    with tab1:
        st.subheader("Top Items by Revenue")
        top_revenue = summary_amount.nlargest(20, 'Amount')
        fig = px.bar(
            top_revenue,
            y='Amount',
            title='Top 20 Items by Revenue',
            labels={'Amount': 'Total Revenue ($)'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Top Items by Quantity Sold")
        top_count = summary_amount.nlargest(20, 'Count')
        fig = px.bar(
            top_count,
            y='Count',
            title='Top 20 Items by Quantity Sold',
            labels={'Count': 'Total Units Sold'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Monthly trends
    st.subheader("Monthly Sales Trends")
    monthly_totals = sales_data.groupby('Month').agg({
        'Amount': 'sum',
        'Count': 'sum'
    }).reset_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.line(
            monthly_totals,
            x='Month',
            y='Amount',
            title='Monthly Revenue Trend',
            labels={'Amount': 'Total Revenue ($)'}
        )
        st.plotly_chart(fig)
    
    with col2:
        fig = px.line(
            monthly_totals,
            x='Month',
            y='Count',
            title='Monthly Sales Volume Trend',
            labels={'Count': 'Total Units Sold'}
        )
        st.plotly_chart(fig)