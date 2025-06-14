import pandas as pd
import matplotlib.pyplot as plt
import json
from datetime import datetime

df = pd.read_csv('merged.csv')
df['date'] = pd.to_datetime(df['date'])

with open('summary_stats.json', 'r') as f:
    stats = json.load(f)

fig, axes = plt.subplots(2, 2, figsize=(15, 12))
fig.suptitle('Sales Data Visualization', fontsize=16)

ax1 = axes[0, 0]
product_counts = df['product'].value_counts()
ax1.bar(product_counts.index, product_counts.values)
ax1.set_title('Product Distribution')
ax1.set_xlabel('Product')
ax1.set_ylabel('Count')
ax1.set_xticklabels(product_counts.index, rotation=45)

ax2 = axes[0, 1]
ax2.hist(df['quantity'], bins=10, edgecolor='black')
ax2.set_title('Quantity Distribution')
ax2.set_xlabel('Quantity')
ax2.set_ylabel('Frequency')
ax2.axvline(stats['quantity']['mean'], color='red', linestyle='--', label=f"Mean: {stats['quantity']['mean']:.1f}")
ax2.legend()

ax3 = axes[1, 0]
product_revenue = df.groupby('product').apply(lambda x: (x['quantity'] * x['price']).sum())
ax3.bar(product_revenue.index, product_revenue.values)
ax3.set_title('Revenue by Product')
ax3.set_xlabel('Product')
ax3.set_ylabel('Revenue ($)')
ax3.set_xticklabels(product_revenue.index, rotation=45)

ax4 = axes[1, 1]
daily_sales = df.groupby('date')['quantity'].sum()
ax4.plot(daily_sales.index, daily_sales.values, marker='o')
ax4.set_title('Daily Sales Quantity')
ax4.set_xlabel('Date')
ax4.set_ylabel('Total Quantity')
ax4.tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('sales_visualization.png', dpi=300, bbox_inches='tight')
plt.show()

print("\nSummary Statistics:")
print(f"Total Records: {len(df)}")
print(f"Date Range: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
print(f"Total Revenue: ${(df['quantity'] * df['price']).sum():.2f}")
print(f"Average Order Value: ${(df['quantity'] * df['price']).mean():.2f}")
print(f"\nProduct Performance:")
for product in df['product'].unique():
    product_data = df[df['product'] == product]
    revenue = (product_data['quantity'] * product_data['price']).sum()
    avg_quantity = product_data['quantity'].mean()
    print(f"  {product}: ${revenue:.2f} revenue, {avg_quantity:.1f} avg quantity")