import os
import pandas as pd

from customer_cleaner import CustomerCleaner


# ============================================================
# Load Dataset
# ============================================================

csv_path = "customer_churn.csv"
df = pd.read_csv(csv_path)

# ============================================================
# Clean Dataset
# ============================================================

clean_df = CustomerCleaner(df).clean()

print("=" * 60)
print("FEATURE ENGINEERING")
print("=" * 60)

print(clean_df.head())

# ============================================================
# Feature 1 - Tenure Bucket
# ============================================================

clean_df["tenure_bucket"] = pd.cut(
    clean_df["tenure"],
    bins=[0, 12, 24, 48, 72],
    labels=["0-12", "13-24", "25-48", "49-72"],
    include_lowest=True
)

# ============================================================
# Feature 2 - High Charge Flag
# ============================================================

median_charge = clean_df["monthly_charges"].median()

clean_df["high_charge_flag"] = (
    clean_df["monthly_charges"] > median_charge
).astype(int)

# ============================================================
# Feature 3 - Service Count
# ============================================================

service_columns = [
    "online_security",
    "online_backup",
    "device_protection",
    "tech_support",
    "streaming_tv",
    "streaming_movies"
]

clean_df["service_count"] = clean_df[service_columns].sum(axis=1)

# ============================================================
# Feature 4 - Long Term Customer
# ============================================================

clean_df["is_long_term_customer"] = (
    clean_df["tenure"] >= 24
).astype(int)

# ============================================================
# Feature 5 - Streaming Bundle
# ============================================================

clean_df["has_streaming_bundle"] = (
    (clean_df["streaming_tv"] == 1)
    &
    (clean_df["streaming_movies"] == 1)
).astype(int)

# ============================================================
# Feature 6 - Auto Pay Flag
# ============================================================

clean_df["auto_pay_flag"] = (
    clean_df["payment_method"]
    .str.contains("automatic", case=False)
).astype(int)

print("\n" + "=" * 60)
print("ENGINEERED FEATURES")
print("=" * 60)

print(
    clean_df[
        [
            "tenure_bucket",
            "high_charge_flag",
            "service_count",
            "is_long_term_customer",
            "has_streaming_bundle",
            "auto_pay_flag"
        ]
    ].head()
)

# ============================================================
# Correlation with Churn
# ============================================================

feature_columns = [
    "high_charge_flag",
    "service_count",
    "is_long_term_customer",
    "has_streaming_bundle",
    "auto_pay_flag"
]

print("\n" + "=" * 60)
print("CORRELATION WITH CHURN")
print("=" * 60)

correlation = clean_df[feature_columns + ["churn"]].corr()["churn"].drop("churn")

print(correlation.sort_values(ascending=False).round(4))

# ============================================================
# Save Feature Dataset
# ============================================================

output_path = "customer_features.csv"


clean_df.to_csv(
    output_path,
    index=False
)

print("\nFeature dataset saved successfully!")
print(f"Location: {output_path}")