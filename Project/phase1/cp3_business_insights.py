import pandas as pd

from customer_cleaner import CustomerCleaner


# -------------------------
# Load Dataset
# -------------------------

csv_path = "customer_churn.csv"
df = pd.read_csv(csv_path)

# -------------------------
# Clean Dataset
# -------------------------

clean_df = CustomerCleaner(df).clean()

print("=" * 60)
print("DATA LOADED & CLEANED")
print("=" * 60)

print(clean_df.head())

# ============================================================
# 1. Churn Rate by Contract Type
# ============================================================

print("\n" + "=" * 60)
print("CHURN RATE BY CONTRACT TYPE")
print("=" * 60)

contract_churn = (
    clean_df
    .groupby("contract")["churn"]
    .mean()
    .mul(100)
    .round(2)
    .sort_values(ascending=False)
)

print(contract_churn)

highest_contract = contract_churn.idxmax()

print(f"\nHighest churn contract: {highest_contract}")

# ============================================================
# 2. Churn Rate by Internet Service
# ============================================================

print("\n" + "=" * 60)
print("CHURN RATE BY INTERNET SERVICE")
print("=" * 60)

internet_churn = (
    clean_df
    .groupby("internet_service")["churn"]
    .mean()
    .mul(100)
    .round(2)
    .sort_values(ascending=False)
)

print(internet_churn)

highest_internet = internet_churn.idxmax()

print(f"\nHighest churn internet service: {highest_internet}")

# ============================================================
# 3. Churn Rate by Payment Method
# ============================================================

print("\n" + "=" * 60)
print("CHURN RATE BY PAYMENT METHOD")
print("=" * 60)

payment_churn = (
    clean_df
    .groupby("payment_method")["churn"]
    .mean()
    .mul(100)
    .round(2)
    .sort_values(ascending=False)
)

print(payment_churn)

highest_payment = payment_churn.idxmax()

print(f"\nHighest churn payment method: {highest_payment}")

# ============================================================
# 4. Churn Rate by Tenure Bucket
# ============================================================

print("\n" + "=" * 60)
print("CHURN RATE BY TENURE BUCKET")
print("=" * 60)

clean_df["tenure_bucket"] = pd.cut(
    clean_df["tenure"],
    bins=[0, 12, 24, 48, 72],
    labels=["0-12", "13-24", "25-48", "49-72"],
    include_lowest=True
)

tenure_churn = (
    clean_df
    .groupby("tenure_bucket", observed=False)["churn"]
    .mean()
    .mul(100)
    .round(2)
)

print(tenure_churn)

highest_bucket = tenure_churn.idxmax()

print(f"\nHighest churn tenure bucket: {highest_bucket}")

# ============================================================
# 5. Average Monthly Charges by Churn Status
# ============================================================

print("\n" + "=" * 60)
print("AVERAGE MONTHLY CHARGES BY CHURN STATUS")
print("=" * 60)

avg_monthly = (
    clean_df
    .groupby("churn")["monthly_charges"]
    .mean()
    .round(2)
)

avg_monthly.index = [
    "Not Churned",
    "Churned"
]

print(avg_monthly)

# ============================================================
# 6. Highest Churn Combination
# ============================================================

print("\n" + "=" * 60)
print("CHURN RATE BY CONTRACT + INTERNET SERVICE")
print("=" * 60)

segment_churn = (
    clean_df
    .groupby(
        ["contract", "internet_service"],
        observed=False
    )["churn"]
    .mean()
    .mul(100)
    .round(2)
    .sort_values(ascending=False)
)

print(segment_churn)

highest_segment = segment_churn.index[0]

print(f"\nHighest risk segment: {highest_segment}")

print("\n" + "=" * 60)
print("BUSINESS SUMMARY")
print("=" * 60)

print(
    f"1. Customers with {contract_churn.idxmax()} contracts have the highest churn rate "
    f"({contract_churn.max():.2f}%), while {internet_churn.idxmax()} internet users "
    f"show the highest churn among internet service types ({internet_churn.max():.2f}%)."
)

print(
    f"2. Customers paying through {payment_churn.idxmax()} have the highest payment-method "
    f"churn rate ({payment_churn.max():.2f}%), and customers in the {tenure_churn.idxmax()} "
    f"tenure bucket are the most likely to leave ({tenure_churn.max():.2f}%)."
)

contract, internet = highest_segment

print(
    f"3. The highest-risk customer segment is {contract} customers using {internet} "
    "internet service. The retention team should prioritize this group with targeted "
    "offers and proactive engagement."
)