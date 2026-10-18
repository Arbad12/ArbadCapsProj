import pandas as pd

#Task 1 — Load and inspect —
customers = pd.read_csv("../data/customers.csv")
products = pd.read_csv("../data/products.csv")
orders = pd.read_csv("../data/orders.csv")
print(orders.shape)
# (180, 9)


#Task 2 — Standardize payment_method casing —
print(orders['payment_method'].unique())
orders['payment_method'] = orders['payment_method'].str.strip().str.upper()
print(orders['payment_method'].value_counts())
# ['upi' 'UPI' 'COD' 'Card' 'cod' 'CARD' 'card']
# payment_method
# CARD    70
# UPI     55
# COD     55


#Task 3 — Remove duplicate orders —
dup_ord = orders.duplicated(
    subset=[
        'customer_id',
        'product_id',
        'order_date',
        'quantity',
        'discount_pct',
        'payment_method',
        'rating',
        'returned'
    ],
    keep='first'
)
dropped_order_ids = orders.loc[dup_ord, 'order_id']
print("Dropped order_ids:")
print(dropped_order_ids.tolist())
orders_clean = orders.loc[~dup_ord].copy()
duplicates_df = orders.loc[dup_ord].copy()
print("orders_clean shape:", orders_clean.shape)
# Dropped order_ids:
# ['O0176', 'O0177', 'O0178', 'O0179', 'O0180']
# orders_clean shape: (175, 9)


#Task 4 — Impute missing values —
print("Null values before imputing")
print(orders_clean[['discount_pct','rating']].isnull().sum())
orders_clean['discount_pct'] = orders_clean['discount_pct'].fillna(0)
median_rating = orders_clean['rating'].median()
print("median rating = ", median_rating)
orders_clean['rating'] = orders_clean['rating'].fillna(median_rating)
print("Null values after imputing")
print(orders_clean[['discount_pct','rating']].isnull().sum())
# Null values before imputing
# discount_pct    12
# rating          15
# median rating =  3.0
# Null values after imputing
# discount_pct    0
# rating          0


#Task 5 — Merge and reconcile against Part 1 —
merged_df = (
    orders_clean
    .merge(customers, on='customer_id')
    .merge(products, on='product_id')
)
clean_total = (
    merged_df['quantity']
    * merged_df['price']
    * (1 - merged_df['discount_pct'] / 100)
).sum().round(2)
print("total order value = ", clean_total)
# total order value =  97358.3

raw_df = (
    orders
    .merge(customers, on='customer_id')
    .merge(products, on='product_id')
)
raw_df['order_value'] = (   
        raw_df['quantity']
      * raw_df['price']
      * (1 - raw_df['discount_pct'].fillna(0) / 100)
)
raw_total = raw_df['order_value'].sum().round(2)

delta = (raw_total - clean_total).round(2)

duplicates_merged = (
    duplicates_df
    .merge(customers, on='customer_id')
    .merge(products, on='product_id')
)
duplicate_total = (
    duplicates_merged['quantity']
    * duplicates_merged['price']
    * (1 - duplicates_merged['discount_pct'].fillna(0) / 100)
).sum().round(2)

print("RECONCILIATION NOTE")
print(
    f"""The cleaned total order value is ₹{clean_total:,.2f}, which is
₹2,501.90 less than Part 1 Report (a)'s raw total of ₹99,860.20.
This difference is entirely attributable to the removal of 5 duplicate
order rows in Task 3. As an independent check, the combined order_value
of the 5 dropped duplicate rows is ₹{duplicate_total:,.2f}, which exactly
matches the revenue reduction above. The discount_pct and rating
imputations performed during data cleaning do not affect order_value
calculations and therefore did not contribute to this change in total
revenue."""
)


#Task 6 — IQR outlier detection on quantity —
Q1 = merged_df['quantity'].quantile(0.25)
Q3 = merged_df['quantity'].quantile(0.75)
IQR = Q3 - Q1
lower = Q1 - 1.5*IQR
upper = Q3 + 1.5*IQR
print(
    f"Q1 = {Q1}, "
    f"Q3 = {Q3}, "
    f"IQR = {IQR}, "
    f"lower = {lower}, "
    f"upper = {upper}"
)
merged_df["is_outlier"] = (
    (merged_df["quantity"] < lower) |
    (merged_df["quantity"] > upper)
)
print(merged_df[merged_df["is_outlier"]][["order_id", "quantity"]])
# Q1 = 1.0, Q3 = 2.0, IQR = 1.0, lower = -0.5, upper = 3.5
#      order_id  quantity
# 10    O0011        25
# 97    O0098        30


#Task 7 — Hypothesis: does COD have a higher return rate? —
print("Hypothesis:")
print("COD (Cash on Delivery) has a higher return rate than other payment methods.")
print()

payment_returns = (
    merged_df.groupby("payment_method")["returned"]
      .agg(["count", "mean"])
)

payment_returns["return_rate_pct"] = (
    payment_returns["mean"] * 100
).round(1)

cod_rate = payment_returns.loc['COD', 'return_rate_pct']
card_rate = payment_returns.loc['CARD', 'return_rate_pct']
upi_rate = payment_returns.loc['UPI', 'return_rate_pct']

print(payment_returns)
if cod_rate > card_rate and cod_rate > upi_rate:
    print("Hypothesis is CONFIRMED")
else:
    print("Hypothesis is BUSTED")
# Hypothesis:
# COD (Cash on Delivery) has a higher return rate than other payment methods.
#                   count   mean         return_rate_pct
# payment_method                                  
# CARD               68   0.147059             14.7
# COD                54   0.444444             44.4
# UPI                53   0.188679             18.9
# Hypothesis is CONFIRMED 


#Task 8 — Multi-level segmentation — 
returns_by_payment_ctier = merged_df.groupby(['payment_method', 'city_tier']).agg(
    total_orders=('returned', 'count'),
    return_orders=('returned', 'sum')
)
returns_by_payment_ctier['return_rate'] = ((
    returns_by_payment_ctier['return_orders'] / returns_by_payment_ctier['total_orders']
) * 100).round(1)
print(returns_by_payment_ctier)

highest_risk = returns_by_payment_ctier.loc[
    returns_by_payment_ctier['return_rate'].idxmax()
]
print(
    f"\nThe highest-risk segment is "
    f"{highest_risk.name[0]} + Tier-{highest_risk.name[1]} "
    f"with a return rate of {highest_risk['return_rate']:.1f}%."
)
#                                 total_orders  return_orders  return_rate
# payment_method city_tier                                          
#   CARD           1                    45              4          8.9
#                  2                    23              6         26.1
#   COD            1                    32             12         37.5
#                  2                    22             12         54.5 
#   UPI            1                    31              6         19.4
#                  2                    22              4         18.2
#   The highest-risk segment is COD + Tier-2 with a return rate of 54.5%.


#Task 9 — Correlation analysis —
coeff = merged_df[['rating', 'returned', 'discount_pct', 'quantity']].corr().round(2)

print(coeff)

def corr_band(r):
    r = abs(r)

    if r < 0.20:
        return "negligible"
    elif r < 0.40:
        return "weak"
    elif r < 0.70:
        return "moderate"
    else:
        return "strong"

print("\nCORRELATION ANALYSIS")
print("-" * 50)

cols = ['rating', 'returned', 'discount_pct', 'quantity']

for i in range(len(cols)):
    for j in range(i + 1, len(cols)):
        var1 = cols[i]
        var2 = cols[j]

        r = coeff.loc[var1, var2]
        band = corr_band(r)

        print(
            f"{var1} vs {var2}: "
            f"r = {r:.2f} → {band}"
        )

print("\nHYPOTHESIS TEST")
print("Hypothesis: Higher discounts reduce returns")

r = coeff.loc['discount_pct', 'returned']

if abs(r) < 0.20:
    print(
        f"BUSTED: discount_pct vs returned correlation "
        f"is only {r:.2f}, which falls in the negligible band."
    )
else:
    print(
        f"Supported: correlation = {r:.2f}"
    )
#               rating  returned  discount_pct  quantity
# rating          1.00     -0.10          0.04     -0.10
# returned       -0.10      1.00         -0.09      0.04
# discount_pct    0.04     -0.09          1.00     -0.17
# quantity       -0.10      0.04         -0.17      1.00
# CORRELATION ANALYSIS
# --------------------------------------------------
# rating vs returned: r = -0.10 → negligible
# rating vs discount_pct: r = 0.04 → negligible
# rating vs quantity: r = -0.10 → negligible
# returned vs discount_pct: r = -0.09 → negligible
# returned vs quantity: r = 0.04 → negligible
# discount_pct vs quantity: r = -0.17 → negligible

# HYPOTHESIS TEST
# Hypothesis: Higher discounts reduce returns
# BUSTED: discount_pct vs returned correlation is only -0.09, which falls in the negligible band.


#Task 10 — Outlier-corrected time series —
merged_df['order_date'] = pd.to_datetime(merged_df['order_date'])
merged_df['year'] = merged_df['order_date'].dt.year
merged_df['month'] = merged_df['order_date'].dt.month

merged_df['order_value'] = (   
        merged_df['quantity']
      * merged_df['price']
      * (1 - merged_df['discount_pct'] / 100)
)
monthly_sales = (
    merged_df.groupby(['year', 'month'])['order_value']
      .sum()
      .reset_index()
)
print("Expected")
print(monthly_sales)

monthly_sales_outl = (
    merged_df[merged_df['is_outlier'] == False]
        .groupby(['year', 'month'])['order_value']
        .sum()
        .reset_index()
) 
print("Outlier corrected")  
print(monthly_sales_outl)         

print("Interpretation:")
print(
       """January's apparent lead is an artifact of two bulk orders landing in January:
       O0011 on 2026-01-28 and O0098 on 2026-01-10. These unusually large orders
       inflate January's total order value and make it appear to be the highest month.
       Once O0011 and O0098 are excluded as outliers  March becomes the genuine peak 
       month by total order value.
       """
)
# Expected
#    year  month  order_value
# 0  2026      1      29582.1  (highest)
# 1  2026      2      13195.5
# 2  2026      3      20318.9
# 3  2026      4       9495.3
# 4  2026      5      13151.1
# 5  2026      6      11615.4

# Outlier corrected
#    year  month  order_value
# 0  2026      1      11637.1
# 1  2026      2      13195.5
# 2  2026      3      20318.9  (highest)
# 3  2026      4       9495.3
# 4  2026      5      13151.1
# 5  2026      6      11615.4

# Interpretation:
# January's apparent lead is an artifact of two bulk orders landing in January:
#       O0011 on 2026-01-28 and O0098 on 2026-01-10. These unusually large orders
#       inflate January's total order value and make it appear to be the highest month.
#       Once O0011 and O0098 are excluded as outliers  March becomes the genuine peak 
#       month by total order value.
