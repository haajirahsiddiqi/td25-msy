import pandas as pd
import streamlit as st
import plotly.express as px
from glob import glob
import os

st.title("Mai Shan Yun Inventory Dashboard")

# Load Base Ingredient Data
# Ingredient.csv file contains ingredient usage per menu item.
ingredients = pd.read_csv('Ingredient.csv')

# Load Monthly Sales Data for all months
# Each month has a csv and combine it into a single Dataframe
monthly_data = []
months = ['may', 'june', 'july', 'august', 'september', 'october']

for month in months:
    file_path = f'csv_files/{month}.csv'
    
    # Check if the monthly CSV exists before loading
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df['Month'] = month.capitalize()  # Add a column for the month name
        monthly_data.append(df)

# Combine all months into one DataFrame
sales_data = pd.concat(monthly_data, ignore_index=True)

# Merge Ingredients with Sales Data
# 'ingredients' has ingredient quantities per dish.
# 'sales_data' has number of items sold (Count) per dish.
# Merge them so each row includes both recipe info and how many were sold.
# merge left_on='Item name' (from ingredients) and right_on='Item Name' (from sales).
merged = pd.merge(
    ingredients,
    sales_data,
    left_on='Item name',
    right_on='Item Name',
    how='right'  # Keep all items from sales data (even if not in ingredients)
)

# Calculate Total Ingredient Usage per Item
# For each ingredient column, multiply ingredient amount by how many items were sold.
ingredient_cols = [col for col in ingredients.columns if col != 'Item name']

# Convert ingredient and count columns to numeric and replace invalids or blanks with 0
for col in ingredient_cols:
    merged[col] = pd.to_numeric(merged[col], errors='coerce').fillna(0)
merged['Count'] = pd.to_numeric(merged['Count'], errors='coerce').fillna(0)

# For each ingredient column, calculate total usage per item (basically multiplying it)
# e.g. if each ramen uses 100g of flour and 20 sold → 2000g total.
for col in ingredient_cols:
    merged[f'{col}_total'] = merged[col] * merged['Count']

# Group all rows by Month and sum up total ingredient usage.
monthly_usage = merged.groupby('Month')[
    [f'{col}_total' for col in ingredient_cols]
].sum()

# Clean up column names (remove "_total" suffix for nicer display)
monthly_usage.columns = [col.replace('_total', '') for col in monthly_usage.columns]
st.write("Months in monthly_usage:", list(monthly_usage.index))

# to select month and number of ingredients to visualize.
st.sidebar.header("Filters")
selected_month = st.sidebar.selectbox("Select Month", months)
n_ingredients = st.sidebar.slider("Number of ingredients to show", 5, 15, 10)

#  Main Visualization Layout (Two Columns)
col1, col2 = st.columns(2)

# ----- LEFT COLUMN: Top Ingredients -----
with col1:
    st.subheader(f"Top {n_ingredients} Ingredients Used - {selected_month.capitalize()}")
    
    # Extract the selected month's data
    month_data = monthly_usage.loc[selected_month.capitalize()]
    
    # Sort descending to get top-used ingredients
    top_ingredients = month_data.sort_values(ascending=False).head(n_ingredients)
    
    # Create bar chart using Plotly
    fig1 = px.bar(
        x=top_ingredients.index,
        y=top_ingredients.values,
        labels={'x': 'Ingredient', 'y': 'Usage'},
        title=f"Top {n_ingredients} Ingredients by Usage"
    )
    st.plotly_chart(fig1)

# ----- RIGHT COLUMN: Least Used Ingredients -----
with col2:
    st.subheader(f"Least {n_ingredients} Used Ingredients - {selected_month.capitalize()}")
    
    # Sort ascending to get least-used ingredients
    bottom_ingredients = month_data.sort_values(ascending=True).head(n_ingredients)
    
    # Create bar chart for least-used
    fig2 = px.bar(
        x=bottom_ingredients.index,
        y=bottom_ingredients.values,
        labels={'x': 'Ingredient', 'y': 'Usage'},
        title=f"Bottom {n_ingredients} Ingredients by Usage"
    )
    st.plotly_chart(fig2)
