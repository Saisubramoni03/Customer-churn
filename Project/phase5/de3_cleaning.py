# ============================================================
# DE3 - BUILD THE CLEANING STAGE
# ============================================================

import os
import sys
import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv


# ============================================================
# 1. PATHS
# ============================================================

# phase5 folder
BASE_DIR = Path(__file__).resolve().parent

# Project root
PROJECT_ROOT = BASE_DIR.parent

# Load .env from project root
load_dotenv(PROJECT_ROOT / ".env")


# ============================================================
# 2. LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# 3. DATABASE CONNECTION
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL not found in .env file."
    )

engine = create_engine(DATABASE_URL)


# ============================================================
# 4. IMPORT CUSTOMER CLEANER
# ============================================================

# Phase 1 contains the CustomerCleaner class.
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from phase1.customer_cleaner import CustomerCleaner
except ImportError as e:
    raise ImportError(
        "Could not import CustomerCleaner from phase1.customer_cleaner.py. "
        "Check the Phase 1 file name and location."
    ) from e


# ============================================================
# 5. CLEAN STAGING
# ============================================================

def clean_staging(engine):
    """
    Read raw data from stg_customer_raw,
    reuse CustomerCleaner,
    and write the cleaned data to cleaned_customers.
    """

    logger.info("Reading data from stg_customer_raw...")

    df = pd.read_sql(
        "SELECT * FROM stg_customer_raw",
        engine
    )

    staging_count = len(df)

    logger.info(
        f"Rows read from stg_customer_raw: {staging_count}"
    )

    if staging_count == 0:
        raise ValueError(
            "stg_customer_raw is empty."
        )

    # --------------------------------------------------------
    # Reuse CustomerCleaner from Phase 1
    # --------------------------------------------------------

    logger.info("Running CustomerCleaner...")

    cleaner = CustomerCleaner(df)

    cleaned_df = cleaner.clean()

    # --------------------------------------------------------
    # Row count check
    # --------------------------------------------------------

    cleaned_count = len(cleaned_df)

    logger.info(
        f"Rows after cleaning: {cleaned_count}"
    )

    assert cleaned_count == staging_count, (
        f"Row count mismatch! "
        f"Staging: {staging_count}, "
        f"Cleaned: {cleaned_count}"
    )

    logger.info("PASS: Row count check")

    # --------------------------------------------------------
    # Write cleaned data
    # --------------------------------------------------------

    cleaned_df.to_sql(
        "cleaned_customers",
        engine,
        if_exists="replace",
        index=False
    )

    logger.info(
        "cleaned_customers table created successfully."
    )

    return cleaned_df


# ============================================================
# 6. DATA QUALITY CHECKS
# ============================================================

def run_quality_checks(df):
    """
    Perform the DE3 data quality checks.
    """

    print("\n")
    print("=" * 60)
    print("DE3 DATA QUALITY REPORT")
    print("=" * 60)

    # --------------------------------------------------------
    # Check 1: customer_id NULL
    # --------------------------------------------------------

    customer_id_nulls = df["customer_id"].isnull().sum()

    if customer_id_nulls == 0:
        print(
            f"PASS: customer_id NULL check "
            f"(NULL count = {customer_id_nulls})"
        )
    else:
        print(
            f"FAIL: customer_id NULL check "
            f"(NULL count = {customer_id_nulls})"
        )

    assert customer_id_nulls == 0

    # --------------------------------------------------------
    # Check 2: monthly_charges NULL
    # --------------------------------------------------------

    monthly_charges_nulls = df["monthly_charges"].isnull().sum()

    if monthly_charges_nulls == 0:
        print(
            f"PASS: monthly_charges NULL check "
            f"(NULL count = {monthly_charges_nulls})"
        )
    else:
        print(
            f"FAIL: monthly_charges NULL check "
            f"(NULL count = {monthly_charges_nulls})"
        )

    assert monthly_charges_nulls == 0

    # --------------------------------------------------------
    # Check 3: churn values
    # --------------------------------------------------------

    invalid_churn = df[
        ~df["churn"].isin([0, 1])
    ]

    invalid_churn_count = len(invalid_churn)

    if invalid_churn_count == 0:
        print(
            f"PASS: churn value check "
            f"(invalid count = {invalid_churn_count})"
        )
    else:
        print(
            f"FAIL: churn value check "
            f"(invalid count = {invalid_churn_count})"
        )

    assert invalid_churn_count == 0

    print("=" * 60)
    print("ALL QUALITY CHECKS PASSED")
    print("=" * 60)


# ============================================================
# 7. BUILD CURATED TABLES
# ============================================================

def build_curated_tables(engine, df):
    """
    Populate the existing Phase 2 tables without dropping them.

    Existing table structures, primary keys and foreign keys
    are preserved.
    """

    logger.info("Building curated tables...")

    with engine.begin() as connection:

        # ====================================================
        # 1. Clear existing data
        # ====================================================

        # IMPORTANT:
        # services has a foreign key to customers.
        # Therefore services must be cleared BEFORE customers.

        connection.execute(
            text("DELETE FROM services")
        )

        connection.execute(
            text("DELETE FROM contracts")
        )

        connection.execute(
            text("DELETE FROM billing")
        )

        connection.execute(
            text("DELETE FROM customer_status")
        )

        connection.execute(
            text("DELETE FROM customers")
        )

        logger.info("Existing curated data cleared.")

        # ====================================================
        # 2. CUSTOMERS
        # ====================================================

        customers_df = df[
            [
                "customer_id",
                "gender",
                "senior_citizen",
                "partner",
                "dependents"
            ]
        ].copy()

        customers_df.to_sql(
            "customers",
            connection,
            if_exists="append",
            index=False
        )

        logger.info(
            f"customers populated: {len(customers_df)} rows"
        )

        # ====================================================
        # 3. CONTRACTS
        # ====================================================

        contracts_df = df[
            [
                "customer_id",
                "contract"
            ]
        ].copy()

        contracts_df = contracts_df.rename(
            columns={
                "contract": "contract_type"
            }
        )

        contracts_df.to_sql(
            "contracts",
            connection,
            if_exists="append",
            index=False
        )

        logger.info(
            f"contracts populated: {len(contracts_df)} rows"
        )

        # ====================================================
        # 4. BILLING
        # ====================================================

        billing_df = df[
            [
                "customer_id",
                "tenure",
                "paperless_billing",
                "payment_method",
                "monthly_charges",
                "total_charges"
            ]
        ].copy()

        # Existing billing table expects paperless_billing
        # as VARCHAR(10), so convert 1/0 back to Yes/No.

        billing_df["paperless_billing"] = (
            billing_df["paperless_billing"]
            .map({
                1: "Yes",
                0: "No"
            })
        )

        billing_df.to_sql(
            "billing",
            connection,
            if_exists="append",
            index=False
        )

        logger.info(
            f"billing populated: {len(billing_df)} rows"
        )

        # ====================================================
        # 5. CUSTOMER STATUS
        # ====================================================

        status_df = df[
            [
                "customer_id",
                "churn"
            ]
        ].copy()

        status_df.to_sql(
            "customer_status",
            connection,
            if_exists="append",
            index=False
        )

        logger.info(
            f"customer_status populated: {len(status_df)} rows"
        )

    logger.info("All curated tables populated successfully.")
# ============================================================
# 8. VERIFY TABLES
# ============================================================

def verify_tables(engine):

    print("\n")
    print("=" * 60)
    print("CURATED TABLE VERIFICATION")
    print("=" * 60)

    tables = [
        "cleaned_customers",
        "customers",
        "contracts",
        "billing",
        "customer_status"
    ]

    for table in tables:

        query = text(
            f"SELECT COUNT(*) AS count FROM {table}"
        )

        with engine.connect() as connection:

            result = connection.execute(query)

            count = result.scalar()

        print(
            f"{table:<25} : {count} rows"
        )

    print("=" * 60)


# ============================================================
# 9. MAIN PIPELINE
# ============================================================

def main():

    print("\n")
    print("=" * 60)
    print("DE3 CLEANING PIPELINE")
    print("=" * 60)

    try:

        # ----------------------------------------------------
        # Step 1: Clean staging
        # ----------------------------------------------------

        cleaned_df = clean_staging(engine)

        # ----------------------------------------------------
        # Step 2: Quality checks
        # ----------------------------------------------------

        run_quality_checks(cleaned_df)

        # ----------------------------------------------------
        # Step 3: Build curated tables
        # ----------------------------------------------------

        build_curated_tables(
            engine,
            cleaned_df
        )

        # ----------------------------------------------------
        # Step 4: Verify
        # ----------------------------------------------------

        verify_tables(engine)

        print("\n")
        print("=" * 60)
        print("DE3 CLEANING COMPLETED SUCCESSFULLY")
        print("=" * 60)

    except Exception as e:

        logger.error(
            f"DE3 FAILED: {e}"
        )

        raise


# ============================================================
# 10. RUN
# ============================================================

if __name__ == "__main__":
    main()