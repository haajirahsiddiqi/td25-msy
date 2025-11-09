import numpy as np
import pandas as pd
import glob
import matplotlib.pyplot as plt
import seaborn as sns

#each month's item and customer spending data
may_df = pd.read_csv('td25-msy/csv_files/may.csv')
jun_df = pd.read_csv('td25-msy/csv_files/june.csv')
jul_df = pd.read_csv('td25-msy/csv_files/july.csv')
aug_df = pd.read_csv('td25-msy/csv_files/august.csv')
sep_df = pd.read_csv('td25-msy/csv_files/september.csv')
oct_df = pd.read_csv('td25-msy/csv_files/october.csv')

may = may_df.copy()
jun = jun_df.copy()
jul = jul_df.copy()
aug = aug_df.copy()
sep = sep_df.copy()
oct = oct_df.copy()

may = may.drop(['source_page', 'source_table'], axis=1)
jun = jun.drop(['source_page', 'source_table'], axis=1)
jul = jul.drop(['source_page', 'source_table'], axis=1)
aug = aug.drop(['source_page', 'source_table'], axis=1)
sep = sep.drop(['source_page', 'source_table'], axis=1)
oct = oct.drop(['source_page', 'source_table'], axis=1)

#combine into 1 df for all time spending and count sold for each item
months_df = pd.concat([may, jun, jul, aug, sep, oct], axis=0)
months_df['Count'] = months_df['Count'].replace(',', '', regex=True).astype(float)
months_df['Amount'] = months_df['Amount'].replace(',', '', regex=True).astype(float)
months_df['Item Name'] = months_df['Item Name'].replace(' ', '\n', regex=True)

#summary of total spending
summary_amount_df = (
    months_df
    .groupby('Item Name', as_index=False)
    .agg({'Count': 'sum', 'Amount': 'sum'})
    .sort_values('Amount', ascending=False)
)
summary_amount_df = summary_amount_df.drop(['Count'], axis = 1)

#summary of total count sold
summary_count_df = (
    months_df
    .groupby('Item Name', as_index=False)
    .agg({'Count': 'sum', 'Amount': 'sum'})
    .sort_values('Count', ascending=False)
)
#remove rows with amount = 0
mask = summary_count_df['Amount'] == 0

#keep rows where amount is not 0
summary_count_df = summary_count_df[~mask]

summary_count_df = summary_count_df.drop(['Amount'], axis = 1)

#Top 20 by Count
t20_count = summary_count_df.head(20)

#Top 20 by Spending
t20_spending = summary_amount_df.head(20)

plt.figure(figsize=(20, 10))
sns.barplot(y='Amount', x='Item Name', data = t20_spending, color = 'orange')
plt.title('All Time Spending for Top 20 Items', fontsize=16, fontweight='bold')
plt.xlabel('Item Name', fontsize=12, fontweight='bold')
plt.ylabel('Total Spending ($)', fontsize=12, fontweight='bold')
plt.show() 

plt.figure(figsize=(20, 10))
sns.barplot(y='Count', x='Item Name', data = t20_count, color = 'purple')
plt.title('All Time Count Sold for Top 20 Items', fontsize=16, fontweight='bold')
plt.xlabel('Item Name', fontsize=12, fontweight='bold')
plt.ylabel('Total Count', fontsize=12, fontweight='bold')
plt.show() 