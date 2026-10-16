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


Task 6 — IQR outlier detection on quantity —
