import logging
import pandas as pd

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os


# ============================================================
# Logging
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# Database Configuration
# ============================================================

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file")

engine = create_engine(DATABASE_URL)


# ============================================================
# Build Features
# ============================================================

def build_features(engine):

    logger.info("Reading data from cleaned_customers...")

    df = pd.read_sql(
        "SELECT * FROM cleaned_customers",
        engine
    )

    logger.info(
        f"Rows read from cleaned_customers: {len(df)}"
    )

    # ========================================================
    # Feature 1 - Tenure Bucket
    # ========================================================

    df["tenure_bucket"] = pd.cut(
        df["tenure"],
        bins=[0, 12, 24, 48, 72],
        labels=["0-12", "13-24", "25-48", "49-72"],
        include_lowest=True
    )

    # ========================================================
    # Feature 2 - High Charge Flag
    # ========================================================

    median_charge = df["monthly_charges"].median()

    logger.info(
        f"Monthly charges median: {median_charge}"
    )

    df["high_charge_flag"] = (
        df["monthly_charges"] > median_charge
    ).astype(int)

    # ========================================================
    # Feature 3 - Service Count
    # ========================================================

    service_columns = [
        "online_security",
        "online_backup",
        "device_protection",
        "tech_support",
        "streaming_tv",
        "streaming_movies"
    ]

    df["service_count"] = (
        df[service_columns].sum(axis=1)
    )

    # ========================================================
    # Feature 4 - Long Term Customer
    # ========================================================

    df["is_long_term_customer"] = (
        df["tenure"] >= 24
    ).astype(int)

    # ========================================================
    # Feature 5 - Streaming Bundle
    # ========================================================

    df["has_streaming_bundle"] = (
        (df["streaming_tv"] == 1)
        &
        (df["streaming_movies"] == 1)
    ).astype(int)

    # ========================================================
    # Feature 6 - Auto Pay Flag
    # ========================================================

    df["auto_pay_flag"] = (
        df["payment_method"]
        .str.contains(
            "automatic",
            case=False,
            na=False
        )
    ).astype(int)

    logger.info("All 6 features generated successfully.")

    # ========================================================
    # Select Required Columns
    # ========================================================

    feature_columns = [
        "customer_id",
        "tenure_bucket",
        "high_charge_flag",
        "service_count",
        "is_long_term_customer",
        "has_streaming_bundle",
        "auto_pay_flag"
    ]

    features_df = df[feature_columns].copy()

    # ========================================================
    # Write Feature Table
    # ========================================================

    features_df.to_sql(
        "customer_ml_features",
        engine,
        if_exists="replace",
        index=False
    )

    logger.info(
        "customer_ml_features table created successfully."
    )

    return features_df


# ============================================================
# Validation
# ============================================================

def validate_features(engine):

    logger.info("Running feature validation...")

    # --------------------------------------------------------
    # Row Count Check
    # --------------------------------------------------------

    cleaned_count = pd.read_sql(
        "SELECT COUNT(*) AS count FROM cleaned_customers",
        engine
    )["count"].iloc[0]

    feature_count = pd.read_sql(
        "SELECT COUNT(*) AS count FROM customer_ml_features",
        engine
    )["count"].iloc[0]

    if cleaned_count == feature_count:
        print(
            f"PASS: Row count check "
            f"({feature_count} == {cleaned_count})"
        )
    else:
        raise AssertionError(
            f"FAIL: Row count mismatch "
            f"({feature_count} != {cleaned_count})"
        )

    # --------------------------------------------------------
    # Feature Column Check
    # --------------------------------------------------------

    expected_features = [
        "tenure_bucket",
        "high_charge_flag",
        "service_count",
        "is_long_term_customer",
        "has_streaming_bundle",
        "auto_pay_flag"
    ]

    table_columns = pd.read_sql(
        """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'customer_ml_features'
        """,
        engine
    )["COLUMN_NAME"].tolist()

    missing_columns = [
        col
        for col in expected_features
        if col not in table_columns
    ]

    if missing_columns:
        raise AssertionError(
            f"Missing feature columns: {missing_columns}"
        )

    print("PASS: All 6 feature columns present")

    # --------------------------------------------------------
    # NULL Check
    # --------------------------------------------------------

    feature_df = pd.read_sql(
        "SELECT * FROM customer_ml_features",
        engine
    )

    null_counts = feature_df[
        expected_features
    ].isnull().sum()

    if null_counts.sum() == 0:
        print("PASS: No NULL values in feature columns")
    else:
        print("FAIL: NULL values found:")
        print(null_counts)

        raise AssertionError(
            "Feature table contains NULL values"
        )

    print("\nFeature validation completed successfully.")


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    print("\n")
    print("=" * 60)
    print("DE4 FEATURE ENGINEERING PIPELINE")
    print("=" * 60)

    try:

        build_features(engine)

        print("\n")
        print("=" * 60)
        print("DE4 FEATURE VALIDATION")
        print("=" * 60)

        validate_features(engine)

        # ----------------------------------------------------
        # Show sample records
        # ----------------------------------------------------

        sample = pd.read_sql(
            """
            SELECT *
            FROM customer_ml_features
            LIMIT 5
            """,
            engine
        )

        print("\nSample feature records:")
        print(sample)

        print("\n")
        print("=" * 60)
        print("DE4 FEATURE PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 60)

    except Exception as e:

        logger.error(
            f"DE4 FAILED: {e}"
        )

        raise