#This file uses variables defined in clean_and_eda.py and is to be RUN second.

import pandas as pd
import matplotlib.pyplot as plt


###    return_rate_by_payment.png — ###

payment_returns = payment_returns.reset_index()

payment_returns = payment_returns.sort_values(
    'return_rate_pct',
    ascending=False
)
# Build insight-driven title
highest = payment_returns.iloc[0]
lowest = payment_returns.iloc[-1]
ratio = highest['return_rate_pct'] / lowest['return_rate_pct']

title = (
    f"{highest['payment_method']} Returns at "
    f"{highest['return_rate_pct']:.1f}% — {ratio:.1f}x "
    f"{lowest['payment_method']}"
)

# Plot
plt.figure(figsize=(8, 5))
bars = plt.bar(
    payment_returns['payment_method'],
    payment_returns['return_rate_pct'],
    color='steelblue'
)

# Value labels
for bar, value in zip(bars, payment_returns['return_rate_pct']):
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        value + 0.5,
        f'{value:.1f}%',
        ha='center',
        fontsize=10
    )

plt.title(title, fontsize=13, weight='bold')
plt.xlabel('Payment Method')
plt.ylabel('Return Rate (%)')
plt.ylim(0, payment_returns['return_rate_pct'].max() * 1.15)
plt.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('return_rate_by_payment.png', dpi=300, bbox_inches='tight')
plt.show()






###   monthly_revenue_trend.png —  ###

# Find peak month
peak_row = monthly_sales_outl.loc[monthly_sales_outl['order_value'].idxmax()]
inflated_row = monthly_sales.loc[monthly_sales['order_value'].idxmax()]
corrected_inflated_row = monthly_sales_outl[monthly_sales_outl['month'] == 1]

title = (
    f"{int(peak_row['year'])}-{int(peak_row['month']):02d} "
    f"Is the Genuine Peak Revenue Month After Outlier Review "
    f"(₹{peak_row['order_value']:,.1f})"
)

# Line chart
plt.figure(figsize=(8,5))

plt.plot(
    monthly_sales_outl['month'],
    monthly_sales_outl['order_value'],
    marker='o',
    linewidth=2
)

# Label each point
for month, value in zip(monthly_sales_outl['month'],
                        monthly_sales_outl['order_value']):
    plt.text(
        month,
        value,
        f'{value:,.0f}',
        ha='center',
        va='bottom'
    )

plt.title(title, fontsize=13, weight='bold')
plt.xlabel('Month')
plt.ylabel('Total Order Value (₹)')
plt.xticks(monthly_sales_outl['month'])
plt.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('monthly_revenue_trend.png', dpi=300)
plt.show()









#  Task 3.1 — narrator/findings.json —

import json
highest_risk_idx = returns_by_payment_ctier['return_rate'].idxmax()

findings = {
    "cleaned_total_revenue_inr": float(clean_total),
    "raw_total_revenue_inr": float(raw_total),
    "duplicate_reconciliation_delta_inr": float(delta),
    "return_rate_by_payment": {
        row["payment_method"]: (row["return_rate_pct"])
        for _, row in payment_returns.iterrows()
    },
    "highest_risk_segment": {
        "payment_method": highest_risk_idx[0],
        "city_tier": int(highest_risk_idx[1]),
        "return_rate_pct": float(highest_risk["return_rate"])
    },
    "true_peak_month": {
        "month": f"{int(peak_row['year'])}-{int(peak_row['month']):02d}",
        "revenue_inr": peak_row['order_value']
    },
    "outlier_inflated_month": {
        "month": f"{int(inflated_row['year'])}-{int(inflated_row['month']):02d}",
        "apparent_revenue_inr": round(inflated_row['order_value'],1),
        "corrected_revenue_inr": corrected_inflated_row['order_value'].iloc[0] 
    }
}

with open("findings.json", "w") as f:
    json.dump(findings, f, indent=4)

print("\nfindings.json exported successfully.")
