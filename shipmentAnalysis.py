
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import glob

######################################## load shipment data ########################################
# print("Loading shipment data...")
shipments = pd.read_csv('Shipment.csv')
# shipments.head()
# print(f"✓ Loaded {len(shipments)} ingredients")

######################################## find total amount of shipments per month ########################################
# quantity * shipment number * frequency
# standardize freqency for all ingredients
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

# calculate and store total shipment
shipments['Shipments per Month'] = shipments['frequency'].apply(monthlyFreq) * shipments['Number of shipments']
shipments['Monthly Quantity (g)'] = shipments['Quantity per shipment'] * shipments['Shipments per Month']

lbs_mask = shipments['Unit of shipment'].str.lower().str.strip() == 'lbs'
shipments.loc[lbs_mask, 'Monthly Quantity (g)'] = shipments.loc[lbs_mask, 'Monthly Quantity (g)'] * 453.59237

######################################## find monthly ingredient usage ########################################
# combine all monthly data into one dataframe
monthlySalesFiles = glob.glob('csv_files/*.csv')
dfs = []
for file in monthlySalesFiles:
    df = pd.read_csv(file)
    # get month name from filename
    monthName = file.split('/')[-1].replace('.csv', '')
    monthName = monthName[10:]
    # print(monthName)
    df['month'] = monthName
    dfs.append(df)

orders = pd.concat(dfs, ignore_index=True)
orders.rename(columns={'Item Name': 'Category'}, inplace=True)

# clean data
# remove commas, convert all to numeric types 
# replace NaN with 0
orders['Count'] = pd.to_numeric(orders['Count'], errors='coerce').fillna(0)
orders['Amount'] = orders['Amount'].astype(str).str.replace(',', '').astype(float)

# print(f"\n✓ Combined data: {len(orders)} total orders across {orders['month'].nunique()} months")

# ######################################## load ingredient data ########################################
# print("\nLoading ingredient mapping...")
ingredients = pd.read_csv('Ingredient.csv')

# column name type for bokchoy
if 'Boychoy(g)' in ingredients.columns:
    ingredients.rename(columns={'Boychoy(g)': 'Bokchoy(g)'}, inplace=True)

ingredients.rename(columns={'Item name': 'Category'}, inplace=True)
# print(f"✓ Loaded {len(ingredients)} ingredient recipes")

######################################## calculate ingredient usage for each month ########################################
# print("\nCalculating ingredient usage...")

# marge tables based on category 
usage = orders.merge(ingredients, on='Category', how='left')

# find ingredient usage based on number of times category item was ordered 
ingredientCols = [col for col in ingredients.columns if col != 'Category']
# make sure values are numeric 
for col in ingredientCols:
    usage[col] = pd.to_numeric(usage[col], errors='coerce').fillna(0)
for col in ingredientCols:
    usage[col] = usage[col] * usage['Count']


######################################## find total ingredient usage ########################################

# sum usage by month name 
monthlyUsage = usage.groupby('month')[ingredientCols].sum()

avgMonthlyUsage = monthlyUsage.mean(axis=0)

######################################## compare usage vs supply ########################################
# print("\nComparing supply vs usage...")

# handle difference in shipment name vs ingredient name
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

# Build comparison dataframe
comparisonData = []

for idx, row in shipments.iterrows():
    ingredientName = row['Ingredient']
    monthlySupply = row['Monthly Quantity (g)']
    
    # get usage for each ingreidient 
    usageCol = ingredientNameMap.get(ingredientName)
    
    if usageCol and usageCol in avgMonthlyUsage.index:
        avgUsage = avgMonthlyUsage[usageCol]
    else:
        avgUsage = 0
        print(f"No usage data found for {ingredientName}")
    
    difference = monthlySupply - avgUsage
    
    # calculate usage and supply levels 
    if avgUsage > 0:
        utilization = (avgUsage / monthlySupply) * 100 if monthlySupply > 0 else 0
        daysOfSupply = (monthlySupply / (avgUsage / 30)) if avgUsage > 0 else 999
    else:
        utilization = 0
        daysOfSupply = 999
    
    comparisonData.append({
        'Ingredient': ingredientName,
        'monthlySupply': monthlySupply,
        'Unit': row['Unit of shipment'],
        'Avg_Monthly_Usage': avgUsage,
        'Difference': difference,
        'Utilization_%': utilization,
        'daysOfSupply': daysOfSupply,
        'Status': 'CRITICAL' if daysOfSupply < 5 else 'LOW' if daysOfSupply < 10 else 'GOOD' if daysOfSupply < 45 else 'OVERSTOCKED'
    })

comparison = pd.DataFrame(comparisonData)

print("\n" + "="*80)
print("SUPPLY vs USAGE COMPARISON")
print("="*80)
print(comparison.to_string(index=False))

######################################## visualizations ########################################
# Figure 1: Monthly Supply by Ingredient
plt.figure(figsize=(20, 8))
shipments_sorted = shipments.sort_values('Monthly Quantity (g)', ascending=True)
sns.barplot(data=shipments_sorted, y='Ingredient', x='Monthly Quantity (g)', palette='viridis')
plt.title('Estimated Monthly Supply per Ingredient', fontsize=16, fontweight='bold')
plt.xlabel('Monthly Quantity (g)', fontsize=12)
plt.ylabel('Ingredient', fontsize=12)
plt.tight_layout()
plt.savefig('monthlySupply.png', dpi=300, bbox_inches='tight')
print("✓ Saved: monthlySupply.png")
plt.show()

# Figure 2: Supply vs Usage Gap Analysis
plt.figure(figsize=(20, 8))
comparison_sorted = comparison.sort_values('Difference', ascending=True)
colors = ['red' if x < 0 else 'green' for x in comparison_sorted['Difference']]
sns.barplot(data=comparison_sorted, y='Ingredient', x='Difference', palette=colors)
plt.axvline(0, color='black', linestyle='--', linewidth=2)
plt.title('Supply Gap Analysis (Negative = Shortage Risk)', fontsize=16, fontweight='bold')
plt.xlabel('Difference (Supply - Usage)', fontsize=12)
plt.ylabel('Ingredient', fontsize=12)
plt.tight_layout()
plt.savefig('supply_gap.png', dpi=300, bbox_inches='tight')
print("✓ Saved: supply_gap.png")
plt.show()

# Figure 3: Utilization Rate
plt.figure(figsize=(20, 8))
comparison_sorted = comparison.sort_values('Utilization_%', ascending=False)
colors_util = ['red' if x > 90 else 'orange' if x > 50 else 'green' for x in comparison_sorted['Utilization_%']]
sns.barplot(data=comparison_sorted, y='Ingredient', x='Utilization_%', palette=colors_util)
plt.axvline(100, color='red', linestyle='--', linewidth=2, label='100% Utilization')
plt.title('Ingredient Utilization Rate', fontsize=16, fontweight='bold')
plt.xlabel('Utilization (%)', fontsize=12)
plt.ylabel('Ingredient', fontsize=12)
plt.legend()
plt.tight_layout()
plt.savefig('utilization_rate.png', dpi=300, bbox_inches='tight')
print("✓ Saved: utilization_rate.png")
plt.show()

######################################## summary of data ########################################
print("\n" + "="*80)
print("KEY INSIGHTS")
print("="*80)

critical_items = comparison[comparison['Status'] == 'CRITICAL']
if not critical_items.empty:
    print("\nCRITICAL ITEMS (Need immediate attention):")
    for _, item in critical_items.iterrows():
        print(f"   • {item['Ingredient']}: Only {item['daysOfSupply']:.1f} days supply remaining")

low_items = comparison[comparison['Status'] == 'LOW']
if not low_items.empty:
    print("\nLOW STOCK ITEMS (Reorder within 10 days):")
    for _, item in low_items.iterrows():
        print(f"   • {item['Ingredient']}: {item['daysOfSupply']:.1f} days supply")

overstocked = comparison[comparison['Status'] == 'OVERSTOCKED']
if not overstocked.empty:
    print("\nOVERSTOCKED ITEMS (Consider reducing orders):")
    for _, item in overstocked.iterrows():
        print(f"   • {item['Ingredient']}: {item['daysOfSupply']:.1f} days supply ({item['Utilization_%']:.1f}% utilization)")
