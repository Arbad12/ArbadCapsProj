import pandas as pd

#Task 1 — Load and inspect —
customers = pd.read_csv("../data/customers.csv")
products = pd.read_csv("../data/products.csv")
orders = pd.read_csv("../data/orders.csv")

print(orders.shape)


#Task 2 — Standardize payment_method casing —
