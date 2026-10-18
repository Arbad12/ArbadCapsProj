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

duplicates_merged = (
    duplicates_df
    .merge(customers, on='customer_id')
    .merge(products, on='product_id')
)
duplicate_total = (
    duplicates_merged['quantity']
    * duplicates_merged['price']
    * (1 - duplicates_merged['discount_pct'] / 100)
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
print(Q1,Q3,IQR,lower,upper)
merged_df["is_outlier"] = (
    (merged_df["quantity"] < lower) |
    (merged_df["quantity"] > upper)
)
print(merged_df[merged_df["is_outlier"]][["order_id", "quantity"]])
# 1.0 2.0 1.0 -0.5 3.5
#      order_id  quantity
# 10    O0011        25
# 97    O0098        30


#Task 7 — Hypothesis: does COD have a higher return rate? —
print("Hypothesis:")
print("H0: COD (Cash on Delivery) does not have a higher return rate than other payment methods.")
print("H1: COD (Cash on Delivery) has a higher return rate than other payment methods.")
print()

payment_returns = (
    merged_df.groupby("payment_method")["returned"]
      .agg(["count", "mean"])
)

payment_returns["return_rate_pct"] = (
    payment_returns["mean"] * 100
).round(1)

print(payment_returns)
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
#                                 total_orders  return_orders  return_rate
# payment_method city_tier                                          
#   CARD           1                    45              4          8.9
#                  2                    23              6         26.1
#   COD            1                    32             12         37.5
#                  2                    22             12         54.5
#   UPI            1                    31              6         19.4
#                  2                    22              4         18.2


#Task 9 — Correlation analysis —
coeff = merged_df[['rating','returned', 'discount_pct', 'quantity']].corr().round(2) 
print(coeff)
#               rating  returned  discount_pct  quantity
# rating          1.00     -0.10          0.04     -0.10
# returned       -0.10      1.00         -0.09      0.04
# discount_pct    0.04     -0.09          1.00     -0.17
# quantity       -0.10      0.04         -0.17      1.00
# Correlation coefficient of all six pairs (-0.10, 0.04, -0.10, -0.09, 0.04, -0.17) fall in negligible (|r| < 0.2) range
# Hypothesis "higher discounts reduce returns" is BUSTED as (discount_pct vs returned correlation ≈ -0.09)


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
print("including outlier")
print(monthly_sales)

monthly_sales_outl = (
    merged_df[merged_df['is_outlier'] == False]
        .groupby(['year', 'month'])['order_value']
        .sum()
        .reset_index()
) 
print("excluding outlier")  
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
# including outlier
#    year  month  order_value
# 0  2026      1      29582.1  (highest)
# 1  2026      2      13195.5
# 2  2026      3      20318.9
# 3  2026      4       9495.3
# 4  2026      5      13151.1
# 5  2026      6      11615.4

# excluding outlier
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
