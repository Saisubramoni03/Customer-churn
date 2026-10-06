import pandas as pd

from customer_cleaner import CustomerCleaner

csv_path = "customer_churn.csv"

df = pd.read_csv(csv_path)

print("=" * 60)
print("BEFORE CLEANING")
print("=" * 60)

print("\nShape:")
print(df.shape)

print("\nColumn Names:")
print(df.columns.tolist())

print("\nData Types:")
print(df.dtypes)

# Clean the dataset
cleaner = CustomerCleaner(df)
clean_df = cleaner.clean()

print("\n" + "=" * 60)
print("AFTER CLEANING")
print("=" * 60)

print("\nShape:")
print(clean_df.shape)

print("\nColumn Names:")
print(clean_df.columns.tolist())

print("\nData Types:")
print(clean_df.dtypes)