import pandas as pd

# =====================================================
# Load Dataset
# =====================================================

csv_path = "customer_churn.csv"

df = pd.read_csv(csv_path)

# =====================================================
# 1. Print Shape
# =====================================================

print("Shape:", df.shape)

# =====================================================
# 2. Print Column Names and Data Types
# =====================================================

print("\nColumns and Data Types:")
print(df.dtypes)

# =====================================================
# 3. Null Values (Before Conversion)
# =====================================================

print("\nNull Values (Original Dataset):")

null_counts = df.isnull().sum()
null_percent = (null_counts / len(df)) * 100

null_summary = pd.DataFrame({
    "Null Count": null_counts,
    "Null Percentage": null_percent.round(2)
})

print(null_summary)

# =====================================================
# 4. Categorical Columns Analysis
# =====================================================

categorical_columns = [
    "gender",
    "Partner",
    "Dependents",
    "PhoneService",
    "InternetService",
    "Contract",
    "PaymentMethod",
    "Churn"
]

for column in categorical_columns:
    print("\n" + "=" * 60)
    print(column)
    print("=" * 60)

    print("Unique Values:")
    print(df[column].unique())

    print("\nValue Counts:")
    print(df[column].value_counts())

# =====================================================
# 5. Churn Distribution
# =====================================================

print("\nChurn Distribution")

churn_counts = df["Churn"].value_counts()
print(churn_counts)

print("\nChurn Percentage")

churn_percentage = (
    df["Churn"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)

print(churn_percentage)

# =====================================================
# 6. Inspect TotalCharges
# =====================================================

print("\nTotalCharges Data Type (Before Conversion)")
print(df["TotalCharges"].dtype)

total_charges_numeric = pd.to_numeric(
    df["TotalCharges"],
    errors="coerce"
)

print("\nNaN Values After Conversion:")
print(total_charges_numeric.isnull().sum())

# Replace the original column with numeric values
df["TotalCharges"] = total_charges_numeric

# =====================================================
# Updated Null Analysis
# =====================================================

print("\nNull Values (After TotalCharges Conversion)")

null_counts = df.isnull().sum()
null_percent = (null_counts / len(df)) * 100

null_summary = pd.DataFrame({
    "Null Count": null_counts,
    "Null Percentage": null_percent.round(2)
})

print(null_summary)

# =====================================================
# 7. Numerical Statistics
# =====================================================

print("\nStatistics")

print("\nTenure")
print("Minimum:", df["tenure"].min())
print("Maximum:", df["tenure"].max())
print("Mean:", round(df["tenure"].mean(), 2))

print("\nMonthlyCharges")
print("Minimum:", df["MonthlyCharges"].min())
print("Maximum:", df["MonthlyCharges"].max())
print("Mean:", round(df["MonthlyCharges"].mean(), 2))

print("\nTotalCharges")
print("Minimum:", df["TotalCharges"].min())
print("Maximum:", df["TotalCharges"].max())
print("Mean:", round(df["TotalCharges"].mean(), 2))

# =====================================================
# 8. Data Profiling Summary
# =====================================================

print("\n" + "=" * 60)
print("DATA PROFILING SUMMARY")
print("=" * 60)

print(f"• Dataset contains {len(df)} records and {df.shape[1]} columns.")
print(f"• TotalCharges has {df['TotalCharges'].isnull().sum()} missing values after numeric conversion.")
print(f"• Churn rate: {churn_percentage['Yes']:.2f}%")
print("• Categorical columns contain a limited number of unique values.")
print("• customerID should be excluded from ML because it is an identifier.")