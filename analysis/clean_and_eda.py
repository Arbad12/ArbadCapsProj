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
