import os
import sys
import logging

import pandas as pd
from sqlalchemy import text


# ============================================================
# IMPORT DATABASE CONNECTION FROM PHASE 5
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

PHASE5_PATH = os.path.join(
    PROJECT_ROOT,
    "phase5"
)

if PHASE5_PATH not in sys.path:
    sys.path.insert(0, PHASE5_PATH)

from db import engine # type: ignore


# ============================================================
# CONFIGURATION
# ============================================================

TABLE_NAME = "cleaned_customers"


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# LOAD CLEANED CUSTOMER DATA
# ============================================================

def load_cleaned_customers():
    logger.info("Loading cleaned customer data from MySQL...")

    query = text("""
        SELECT *
        FROM cleaned_customers
    """)

    with engine.connect() as connection:
        df = pd.read_sql(query, connection)

    logger.info(f"Rows loaded: {len(df)}")

    return df


# ============================================================
# BUILD ML FEATURES
# ============================================================

def build_ml_features(df):
    """
    Create the feature set required by ML1.
    """

    logger.info("Building customer ML features...")

    ml_df = pd.DataFrame()

    # --------------------------------------------------------
    # Identifier
    # --------------------------------------------------------

    ml_df["customer_id"] = df["customer_id"]

    # --------------------------------------------------------
    # Numeric features
    # --------------------------------------------------------

    ml_df["tenure"] = df["tenure"]

    ml_df["monthly_charges"] = df["monthly_charges"]

    ml_df["total_charges"] = df["total_charges"]

    # --------------------------------------------------------
    # Service count
    # Count active optional services
    # --------------------------------------------------------

    service_columns = [
        "online_security",
        "online_backup",
        "device_protection",
        "tech_support",
        "streaming_tv",
        "streaming_movies"
    ]

    ml_df["service_count"] = df[
        service_columns
    ].sum(axis=1)

    # --------------------------------------------------------
    # High charge flag
    # --------------------------------------------------------

    ml_df["high_charge_flag"] = (
        df["monthly_charges"] > 70
    ).astype(int)

    # --------------------------------------------------------
    # Long-term customer flag
    # --------------------------------------------------------

    ml_df["is_long_term_customer"] = (
        df["tenure"] >= 24
    ).astype(int)

    # --------------------------------------------------------
    # Auto-pay flag
    #
    # Payment methods considered automatic:
    # Electronic check
    # Bank transfer (automatic)
    # Credit card (automatic)
    # --------------------------------------------------------

    ml_df["auto_pay_flag"] = (
        df["payment_method"]
        .isin([
            "Electronic check",
            "Bank transfer (automatic)",
            "Credit card (automatic)"
        ])
        .astype(int)
    )

    # --------------------------------------------------------
    # Streaming bundle
    # --------------------------------------------------------

    ml_df["has_streaming_bundle"] = (
        (
            (df["streaming_tv"] == 1)
            |
            (df["streaming_movies"] == 1)
        )
    ).astype(int)

    # --------------------------------------------------------
    # Categorical features
    # --------------------------------------------------------

    ml_df["contract_type"] = df["contract"]

    ml_df["internet_service"] = df["internet_service"]

    # --------------------------------------------------------
    # Target
    # --------------------------------------------------------

    ml_df["churn"] = df["churn"]

    logger.info(
        f"ML feature rows created: {len(ml_df)}"
    )

    return ml_df


# ============================================================
# SAVE ML FEATURES TO MYSQL
# ============================================================

def save_ml_features(ml_df):

    logger.info(
        "Saving customer_ml_features table..."
    )

    with engine.begin() as connection:

        connection.execute(
            text(
                "DROP TABLE IF EXISTS customer_ml_features"
            )
        )

        connection.execute(
            text("""
                CREATE TABLE customer_ml_features (
                    customer_id VARCHAR(50),
                    tenure INT,
                    monthly_charges DOUBLE,
                    total_charges DOUBLE,
                    service_count INT,
                    high_charge_flag INT,
                    is_long_term_customer INT,
                    auto_pay_flag INT,
                    has_streaming_bundle INT,
                    contract_type VARCHAR(50),
                    internet_service VARCHAR(50),
                    churn INT
                )
            """)
        )

    ml_df.to_sql(
        "customer_ml_features",
        engine,
        if_exists="append",
        index=False
    )

    logger.info(
        "customer_ml_features table created successfully."
    )


# ============================================================
# PREPARE X AND Y
# ============================================================

def prepare_ml_data(ml_df):

    logger.info("Preparing X and y...")

    # --------------------------------------------------------
    # Target
    # --------------------------------------------------------

    y = ml_df["churn"].astype(int)

    # --------------------------------------------------------
    # Drop identifier and target
    # --------------------------------------------------------

    X = ml_df.drop(
        columns=[
            "customer_id",
            "churn"
        ]
    )

    # --------------------------------------------------------
    # One-hot encoding
    # --------------------------------------------------------

    X = pd.get_dummies(
        X,
        columns=[
            "contract_type",
            "internet_service"
        ],
        drop_first=False,
        dtype=int
    )

    return X, y


# ============================================================
# DISPLAY ML1 RESULTS
# ============================================================

def display_results(X, y):

    print("\n" + "=" * 70)
    print("ML1 MACHINE LEARNING PROBLEM DEFINITION")
    print("=" * 70)

    print("\nTARGET:")
    print("churn")

    print("\nDROPPED COLUMN:")
    print("customer_id")

    print("\nNUMERIC FEATURES:")
    numeric_features = [
        "tenure",
        "monthly_charges",
        "total_charges",
        "service_count",
        "high_charge_flag",
        "is_long_term_customer",
        "auto_pay_flag",
        "has_streaming_bundle"
    ]

    for column in numeric_features:
        print(f"  - {column}")

    print("\nCATEGORICAL FEATURES:")
    print("  - contract_type")
    print("  - internet_service")

    print("\nFINAL FEATURE MATRIX X:")
    print(X)

    print("\nTARGET VECTOR y:")
    print(y)

    print("\nSHAPES:")
    print(f"X.shape = {X.shape}")
    print(f"y.shape = {y.shape}")

    print("\nFINAL FEATURE COLUMNS:")

    for column in X.columns:
        print(f"  - {column}")

    print("\nCLASS BALANCE:")
    balance = y.value_counts(
        normalize=True
    ).sort_index()

    print(balance)

    print("\nCLASS COUNTS:")
    print(
        y.value_counts()
        .sort_index()
    )

    print("\nMETRIC DISCUSSION:")
    print(
        "Accuracy should NOT be the primary metric."
    )

    print(
        "A model predicting every customer as "
        "non-churn could achieve about 73% accuracy "
        "without identifying churners."
    )

    print(
        "Recommended primary metrics: "
        "F1-score, precision, and recall for churn=1."
    )

    print("\n" + "=" * 70)
    print("ML1 PROBLEM DEFINITION COMPLETED")
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 70)
    print("ML1 CUSTOMER CHURN PREDICTION")
    print("=" * 70)

    try:

        # 1. Load cleaned data
        df = load_cleaned_customers()

        # 2. Build ML features
        ml_df = build_ml_features(df)

        # 3. Save feature table
        save_ml_features(ml_df)

        # 4. Prepare X and y
        X, y = prepare_ml_data(ml_df)

        # 5. Display results
        display_results(X, y)

    except Exception as e:

        logger.error(
            f"ML1 FAILED: {e}"
        )

        raise


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()