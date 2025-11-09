"""
Mai Shan Yun - Combined Team Inventory Dashboard
Integrates: Inventory Analysis, Shipment Tracking, and Cost Optimization
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import glob
import os

# Page config
st.set_page_config(
    page_title="Mai Shan Yun Inventory Dashboard",
    page_icon="🍜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# DATA LOADING FUNCTIONS
# ============================================
@st.cache_data
def load_all_data():
    """Load all CSV files"""
    
    # Load monthly sales files from csv_files folder
    monthlySalesFiles = glob.glob('csv_files/*.csv')
    dfs = []
    for file in monthlySalesFiles:
        df = pd.read_csv(file)
        monthName = file.split('/')[-1].replace('.csv', '')
        if len(monthName) > 10:
            monthName = monthName[10:]
        df['month'] = monthName
        dfs.append(df)
    
    sales_df = pd.concat(dfs, ignore_index=True)
    sales_df['Count'] = pd.to_numeric(sales_df['Count'], errors='coerce').fillna(0)
    sales_df['Amount'] = sales_df['Amount'].astype(str).str.replace(',', '').astype(float)
    sales_df.rename(columns={'Item Name': 'Category'}, inplace=True)
    
    # Load ingredients
    ingredients_df = pd.read_csv('Ingredient.csv')
    if 'Boychoy(g)' in ingredients_df.columns:
        ingredients_df.rename(columns={'Boychoy(g)': 'Bokchoy(g)'}, inplace=True)
    ingredients_df.rename(columns={'Item name': 'Category'}, inplace=True)
    
    # Load shipments
    shipments_df = pd.read_csv('Shipment.csv')
    
    # Calculate monthly quantities for shipments
    def monthlyFreq(freq):
        if pd.isna(freq):
            return np.nan
        freq = str(freq).lower().strip()
        return 4 if freq == "weekly" else 2 if freq == "biweekly" else 1 if freq == "monthly" else np.nan
    
    shipments_df['Shipments per Month'] = shipments_df['frequency'].apply(monthlyFreq) * shipments_df['Number of shipments']
    shipments_df['Monthly Quantity (g)'] = shipments_df['Quantity per shipment'] * shipments_df['Shipments per Month']
    
    # Convert lbs to grams
    lbs_mask = shipments_df['Unit of shipment'].str.lower().str.strip() == 'lbs'
    shipments_df.loc[lbs_mask, 'Monthly Quantity (g)'] = shipments_df.loc[lbs_mask, 'Monthly Quantity (g)'] * 453.59237
    
    return sales_df, ingredients_df, shipments_df

@st.cache_data
def calculate_ingredient_usage(_sales_df, _ingredients_df):
    """Calculate ingredient usage from sales data"""
    
    usage = _sales_df.merge(_ingredients_df, on='Category', how='left')
    ingredientCols = [col for col in _ingredients_df.columns if col != 'Category']
    
    # Convert and multiply by count
    for col in ingredientCols:
        usage[col] = pd.to_numeric(usage[col], errors='coerce').fillna(0)
        usage[col] = usage[col] * usage['Count']
    
    # Monthly aggregation
    monthlyUsage = usage.groupby('month')[ingredientCols].sum()
    avgUsage = monthlyUsage.mean(axis=0)
    
    return avgUsage, monthlyUsage

@st.cache_data
def calculate_shipment_comparison(_shipments_df, _avg_usage):
    """Calculate supply vs usage comparison"""
    
    ingredientNameMap = {
        'Beef': 'braised beef used (g)',
        'Chicken': 'Braised Chicken(g)',
        'Ramen': 'Ramen (count)',
        'Rice Noodles': 'Rice Noodles(g)',
        'Flour': 'flour (g)',
        'Tapioca Starch': 'Tapioca Starch',
        'Rice': 'Rice(g)',
        'Green Onion': 'Green Onion',
        'White Onion': 'White onion',
        'Cilantro': 'Cilantro',
        'Egg': 'Egg(count)',
        'Peas + Carrot': 'Peas(g)',
        'Bokchoy': 'Bokchoy(g)',
        'Chicken Wings': 'Chicken Wings (pcs)'
    }
    
    comparisonData = []
    
    for idx, row in _shipments_df.iterrows():
        ingredientName = row['Ingredient']
        monthlySupply = row['Monthly Quantity (g)']
        
        usageCol = ingredientNameMap.get(ingredientName)
        
        if usageCol and usageCol in _avg_usage.index:
            avgUsage = _avg_usage[usageCol]
        else:
            avgUsage = 0
        
        difference = monthlySupply - avgUsage
        
        if avgUsage > 0:
            utilization = (avgUsage / monthlySupply) * 100 if monthlySupply > 0 else 0
            daysOfSupply = (monthlySupply / (avgUsage / 30)) if avgUsage > 0 else 999
        else:
            utilization = 0
            daysOfSupply = 999
        
        comparisonData.append({
            'Ingredient': ingredientName,
            'Monthly Supply': monthlySupply,
            'Unit': row['Unit of shipment'],
            'Avg Monthly Usage': avgUsage,
            'Difference': difference,
            'Utilization %': utilization,
            'Days of Supply': daysOfSupply,
            'Status': 'CRITICAL' if daysOfSupply < 5 else 'LOW' if daysOfSupply < 10 else 'GOOD' if daysOfSupply < 45 else 'OVERSTOCKED'
        })
    
    return pd.DataFrame(comparisonData)

# ============================================
# LOAD DATA
# ============================================
try:
    with st.spinner("Loading data..."):
        sales_df, ingredients_df, shipments_df = load_all_data()
        avg_usage, monthly_usage = calculate_ingredient_usage(sales_df, ingredients_df)
        comparison_df = calculate_shipment_comparison(shipments_df, avg_usage)
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.header("Dashboard Navigation")
    
    page = st.radio(
        "Select Analysis:",
        ["Overview", "Inventory Analysis", "Shipment Tracking", "Cost Optimization"]
    )
    
    st.markdown("---")
    
    # Quick stats
    st.subheader("Quick Stats")
    critical_count = len(comparison_df[comparison_df['Status'] == 'CRITICAL'])
    low_count = len(comparison_df[comparison_df['Status'] == 'LOW'])
    
    if critical_count > 0:
        st.error(f"🚨 {critical_count} Critical Items")
    if low_count > 0:
        st.warning(f"⚠️ {low_count} Low Stock Items")
    if critical_count == 0 and low_count == 0:
        st.success("✅ All Stock Levels Good")

# ============================================
# HEADER
# ============================================
st.markdown("""
<div class="main-header">
    <h1>🍜 Mai Shan Yun Inventory Intelligence</h1>
    <p>Comprehensive inventory management and cost analysis</p>
</div>
""", unsafe_allow_html=True)

# ============================================
# PAGE: OVERVIEW
# ============================================
if page == "Overview":
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    total_revenue = sales_df['Amount'].sum()
    total_items = sales_df['Count'].sum()
    critical_ingredients = len(comparison_df[comparison_df['Status'] == 'CRITICAL'])
    low_stock = len(comparison_df[comparison_df['Status'] == 'LOW'])
    
    with col1:
        st.metric("💰 Total Revenue", f"${total_revenue:,.0f}")
    
    with col2:
        st.metric("📦 Items Sold", f"{total_items:,.0f}")
    
    with col3:
        st.metric("🚨 Critical Stock", critical_ingredients)
    
    with col4:
        st.metric("⚠️ Low Stock", low_stock)
    
    st.markdown("---")
    
    # Top items and trends
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top 10 Revenue Drivers")
        top_items = sales_df.groupby('Category')['Amount'].sum().sort_values(ascending=False).head(10).reset_index()
        fig = px.bar(top_items, x='Amount', y='Category', orientation='h', color='Amount', color_continuous_scale='Blues')
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Critical Inventory Items")
        critical_items = comparison_df[comparison_df['Status'].isin(['CRITICAL', 'LOW'])].sort_values('Days of Supply')
        
        if not critical_items.empty:
            fig = px.bar(critical_items, y='Ingredient', x='Days of Supply', orientation='h',
                        color='Status', color_discrete_map={'CRITICAL': '#ef4444', 'LOW': '#f97316'})
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("All inventory levels are good!")
    
    st.markdown("---")
    
    # Key insights
    st.subheader("Key Insights")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        critical = comparison_df[comparison_df['Status'] == 'CRITICAL']
        if not critical.empty:
            st.error("**🚨 Immediate Action Required**")
            for _, item in critical.iterrows():
                st.write(f"• {item['Ingredient']}: {item['Days of Supply']:.1f} days")
        else:
            st.success("**✅ No Critical Items**")
    
    with col2:
        top_item = sales_df.groupby('Category')['Amount'].sum().sort_values(ascending=False).head(1)
        st.info(f"**💰 Top Revenue Driver**\n\n{top_item.index[0]}\n\n${top_item.values[0]:,.0f}")
    
    with col3:
        avg_util = comparison_df['Utilization %'].mean()
        st.warning(f"**📊 Avg Utilization Rate**\n\n{avg_util:.1f}%\n\nTarget: 70-90%")

# ============================================
# PAGE: INVENTORY ANALYSIS
# ============================================
elif page == "Inventory Analysis":
    
    st.subheader("Ingredient Usage Analysis")
    
    # Prepare data for inventory analysis
    months = ['may', 'june', 'july', 'august', 'september', 'october']
    
    # Filters
    col1, col2 = st.columns([1, 3])
    with col1:
        selected_month = st.selectbox("Select Month", months)
    with col2:
        n_ingredients = st.slider("Number of ingredients to show", 5, 15, 10)
    
    st.markdown("---")
    
    # Get data for selected month
    if selected_month in monthly_usage.index:
        month_data = monthly_usage.loc[selected_month]
    else:
        st.warning(f"No data available for {selected_month}")
        st.stop()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"Top {n_ingredients} Used Ingredients")
        top_ingredients = month_data.sort_values(ascending=False).head(n_ingredients)
        
        fig = px.bar(
            x=top_ingredients.index,
            y=top_ingredients.values,
            labels={'x': 'Ingredient', 'y': 'Usage (g)'},
            color=top_ingredients.values,
            color_continuous_scale='Greens'
        )
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader(f"Least {n_ingredients} Used Ingredients")
        bottom_ingredients = month_data[month_data > 0].sort_values(ascending=True).head(n_ingredients)
        
        fig = px.bar(
            x=bottom_ingredients.index,
            y=bottom_ingredients.values,
            labels={'x': 'Ingredient', 'y': 'Usage (g)'},
            color=bottom_ingredients.values,
            color_continuous_scale='Reds'
        )
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Monthly trends
    st.subheader("Ingredient Usage Trends Over Time")
    
    # Get top 5 ingredients overall
    top_5_ingredients = monthly_usage.sum().sort_values(ascending=False).head(5).index
    
    trend_data = monthly_usage[top_5_ingredients].reset_index()
    trend_data = trend_data.melt(id_vars='month', var_name='Ingredient', value_name='Usage')
    
    fig = px.line(trend_data, x='month', y='Usage', color='Ingredient', markers=True)
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

# ============================================
# PAGE: SHIPMENT TRACKING
# ============================================
elif page == "Shipment Tracking":
    
    st.subheader("Shipment Tracking & Supply Analysis")
    
    # Status summary
    col1, col2, col3, col4 = st.columns(4)
    
    status_counts = comparison_df['Status'].value_counts()
    
    with col1:
        critical = status_counts.get('CRITICAL', 0)
        st.metric("🚨 Critical", critical)
    
    with col2:
        low = status_counts.get('LOW', 0)
        st.metric("⚠️ Low Stock", low)
    
    with col3:
        good = status_counts.get('GOOD', 0)
        st.metric("✅ Good", good)
    
    with col4:
        overstock = status_counts.get('OVERSTOCKED', 0)
        st.metric("📦 Overstocked", overstock)
    
    st.markdown("---")
    
    # Comparison table
    st.subheader("Supply vs Usage Comparison")
    
    st.dataframe(
        comparison_df.sort_values('Days of Supply')[
            ['Ingredient', 'Monthly Supply', 'Avg Monthly Usage', 'Difference', 
             'Days of Supply', 'Utilization %', 'Status']
        ].style.format({
            'Monthly Supply': '{:.1f}',
            'Avg Monthly Usage': '{:.1f}',
            'Difference': '{:.1f}',
            'Days of Supply': '{:.1f}',
            'Utilization %': '{:.1f}%'
        }),
        use_container_width=True,
        height=400
    )
    
    st.markdown("---")
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Supply Gap Analysis")
        comparison_sorted = comparison_df.sort_values('Difference')
        colors = ['#ef4444' if x < 0 else '#22c55e' for x in comparison_sorted['Difference']]
        
        fig = go.Figure(go.Bar(
            y=comparison_sorted['Ingredient'],
            x=comparison_sorted['Difference'],
            orientation='h',
            marker=dict(color=colors)
        ))
        fig.add_vline(x=0, line_dash="dash", line_color="black", line_width=2)
        fig.update_layout(height=500, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Utilization Rate")
        comparison_sorted = comparison_df.sort_values('Utilization %', ascending=False)
        
        fig = px.bar(comparison_sorted, y='Ingredient', x='Utilization %', orientation='h',
                     color='Utilization %', color_continuous_scale='RdYlGn')
        fig.add_vline(x=100, line_dash="dash", line_color="red", line_width=2)
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Key insights
    st.subheader("Key Insights")
    
    critical_items = comparison_df[comparison_df['Status'] == 'CRITICAL']
    if not critical_items.empty:
        st.error("**CRITICAL ITEMS (Need immediate attention):**")
        for _, item in critical_items.iterrows():
            st.write(f"• {item['Ingredient']}: Only {item['Days of Supply']:.1f} days supply remaining")
    
    low_items = comparison_df[comparison_df['Status'] == 'LOW']
    if not low_items.empty:
        st.warning("**LOW STOCK ITEMS (Reorder within 10 days):**")
        for _, item in low_items.iterrows():
            st.write(f"• {item['Ingredient']}: {item['Days of Supply']:.1f} days supply")
    
    overstocked = comparison_df[comparison_df['Status'] == 'OVERSTOCKED']
    if not overstocked.empty:
        st.info("**OVERSTOCKED ITEMS (Consider reducing orders):**")
        for _, item in overstocked.iterrows():
            st.write(f"• {item['Ingredient']}: {item['Days of Supply']:.1f} days supply ({item['Utilization %']:.1f}% utilization)")

# ============================================
# PAGE: COST OPTIMIZATION
# ============================================
elif page == "Cost Optimization":
    
    st.subheader("Cost Optimization Analysis")
    
    # Prepare combined data
    combined_df = sales_df.copy()
    combined_df['Item Name'] = combined_df['Category']
    
    # Summary by item
    summary_df = (
        combined_df
        .groupby('Item Name', as_index=False)
        .agg({'Count': 'sum', 'Amount': 'sum'})
        .sort_values('Amount', ascending=False)
    )
    
    # Remove items with 0 amount
    summary_df = summary_df[summary_df['Amount'] > 0]
    
    # KPIs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Revenue", f"${summary_df['Amount'].sum():,.0f}")
    
    with col2:
        st.metric("Total Items Sold", f"{summary_df['Count'].sum():,.0f}")
    
    with col3:
        avg_price = summary_df['Amount'].sum() / summary_df['Count'].sum()
        st.metric("Avg Item Price", f"${avg_price:.2f}")
    
    st.markdown("---")
    
    # Top items visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top 20 Items by Revenue")
        top_20_revenue = summary_df.head(20)
        
        fig = px.bar(
            top_20_revenue,
            y='Amount',
            x='Item Name',
            color='Amount',
            color_continuous_scale='Oranges'
        )
        fig.update_layout(height=500, showlegend=False)
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Top 20 Items by Count Sold")
        top_20_count = summary_df.nlargest(20, 'Count')
        
        fig = px.bar(
            top_20_count,
            y='Count',
            x='Item Name',
            color='Count',
            color_continuous_scale='Purples'
        )
        fig.update_layout(height=500, showlegend=False)
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Revenue distribution
    st.subheader("Revenue Distribution Analysis")
    
    # Calculate percentage contribution
    summary_df['Revenue %'] = (summary_df['Amount'] / summary_df['Amount'].sum() * 100)
    summary_df['Cumulative %'] = summary_df['Revenue %'].cumsum()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top 10 Items Revenue Share")
        top_10 = summary_df.head(10)
        
        fig = px.pie(
            top_10,
            values='Amount',
            names='Item Name',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Pareto Analysis (80/20 Rule)")
        
        # Find how many items contribute to 80% of revenue
        items_80_percent = len(summary_df[summary_df['Cumulative %'] <= 80])
        
        st.metric(
            "Items Contributing 80% of Revenue",
            f"{items_80_percent}",
            delta=f"{(items_80_percent / len(summary_df) * 100):.1f}% of total items"
        )
        
        st.write("**Focus on these high-impact items for maximum ROI**")
        st.dataframe(
            summary_df.head(items_80_percent)[['Item Name', 'Amount', 'Revenue %']].style.format({
                'Amount': '${:,.2f}',
                'Revenue %': '{:.1f}%'
            }),
            height=300
        )
    
    st.markdown("---")
    
    # Recommendations
    st.subheader("Cost Optimization Recommendations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("""
        **Focus Areas:**
        
        • Top 20% of items drive majority of revenue
        • Prioritize inventory for high-revenue items
        • Negotiate bulk discounts for top sellers
        • Ensure these items never face stockouts
        """)
    
    with col2:
        low_performers = summary_df[summary_df['Count'] < summary_df['Count'].quantile(0.25)]
        st.warning(f"""
        **Review Opportunities:**
        
        • {len(low_performers)} items in bottom 25% by volume
        • Consider menu optimization
        • Evaluate profitability of low-volume items
        • Potential for cost reduction
        """)

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 2rem;'>
    <p><strong>🍜 Mai Shan Yun Inventory Intelligence Dashboard</strong></p>
    <p>Built for Datathon Challenge</p>
</div>
""", unsafe_allow_html=True)