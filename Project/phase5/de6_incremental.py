import os
import sys
import logging
from datetime import datetime

import pandas as pd
from sqlalchemy import text


# ============================================================
# ALLOW IMPORTING FROM PHASE1
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

PHASE1_PATH = os.path.join(
    PROJECT_ROOT,
    "phase1"
)

if PHASE1_PATH not in sys.path:
    sys.path.insert(0, PHASE1_PATH)

from db import engine
from customer_cleaner import CustomerCleaner # type: ignore


# ============================================================
# CONFIGURATION
# ============================================================

CSV_PATH = "data/raw/customer_churn.csv"


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# READ AND CLEAN CUSTOMER DATA
# ============================================================

def read_customer_data():

    logger.info("Reading customer data...")

    df = pd.read_csv(CSV_PATH)

    logger.info(f"Rows read from CSV: {len(df)}")

    cleaner = CustomerCleaner(df)

    clean_df = cleaner.clean()

    logger.info(f"Rows after cleaning: {len(clean_df)}")

    return clean_df


# ============================================================
# NORMALIZATION HELPERS
# ============================================================

def normalize_value(value):
    """
    Convert pandas NaN/None into None.
    """

    if pd.isna(value):
        return None

    return value


def normalize_paperless(value):
    """
    Normalize paperless_billing values.

    The CSV after cleaning may contain:
        1 / 0

    while the database may contain:
        Yes / No
    """

    if pd.isna(value):
        return None

    value = str(value).strip().lower()

    if value in ("1", "yes", "true"):
        return "Yes"

    if value in ("0", "no", "false"):
        return "No"

    return str(value)


# ============================================================
# PREPARE CUSTOMER DATA
# ============================================================

def prepare_customers(df):

    return df[
        [
            "customer_id",
            "gender",
            "senior_citizen",
            "partner",
            "dependents"
        ]
    ].copy()


# ============================================================
# PREPARE BILLING DATA
# ============================================================

def prepare_billing(df):

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

    # Normalize paperless billing
    billing_df["paperless_billing"] = (
        billing_df["paperless_billing"]
        .apply(normalize_paperless)
    )

    # Ensure numeric columns are numeric
    billing_df["tenure"] = pd.to_numeric(
        billing_df["tenure"],
        errors="coerce"
    )

    billing_df["monthly_charges"] = pd.to_numeric(
        billing_df["monthly_charges"],
        errors="coerce"
    )

    billing_df["total_charges"] = pd.to_numeric(
        billing_df["total_charges"],
        errors="coerce"
    )

    return billing_df


# ============================================================
# COMPARE VALUES
# ============================================================

def values_equal(value1, value2):

    value1 = normalize_value(value1)
    value2 = normalize_value(value2)

    if value1 is None and value2 is None:
        return True

    if value1 is None or value2 is None:
        return False

    # Numeric comparison
    try:
        if float(value1) == float(value2):
            return True
    except (ValueError, TypeError):
        pass

    return str(value1).strip() == str(value2).strip()


# ============================================================
# INCREMENTAL LOAD
# ============================================================

def incremental_load(engine, df):

    logger.info("Starting incremental customer load...")

    customers_df = prepare_customers(df)
    billing_df = prepare_billing(df)

    rows_inserted = 0
    rows_updated = 0
    rows_unchanged = 0

    # ========================================================
    # LOAD EXISTING CUSTOMERS
    # ========================================================

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT
                    customer_id,
                    gender,
                    senior_citizen,
                    partner,
                    dependents
                FROM customers
            """)
        )

        existing_customer_rows = result.mappings().all()

    existing_customers = {
        row["customer_id"]: dict(row)
        for row in existing_customer_rows
    }

    # ========================================================
    # LOAD EXISTING BILLING
    # ========================================================

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT
                    customer_id,
                    tenure,
                    paperless_billing,
                    payment_method,
                    monthly_charges,
                    total_charges
                FROM billing
            """)
        )

        existing_billing_rows = result.mappings().all()

    existing_billing = {
        row["customer_id"]: dict(row)
        for row in existing_billing_rows
    }

    logger.info(
        f"Existing customers in database: "
        f"{len(existing_customers)}"
    )

    # ========================================================
    # CUSTOMER UPSERT
    # ========================================================

    customer_upsert_sql = text("""
        INSERT INTO customers
        (
            customer_id,
            gender,
            senior_citizen,
            partner,
            dependents
        )
        VALUES
        (
            :customer_id,
            :gender,
            :senior_citizen,
            :partner,
            :dependents
        )
        ON DUPLICATE KEY UPDATE
            gender = VALUES(gender),
            senior_citizen = VALUES(senior_citizen),
            partner = VALUES(partner),
            dependents = VALUES(dependents)
    """)

    # ========================================================
    # BILLING UPSERT
    #
    # IMPORTANT:
    # customer_id has a UNIQUE KEY in billing.
    # ========================================================

    billing_upsert_sql = text("""
        INSERT INTO billing
        (
            customer_id,
            tenure,
            paperless_billing,
            payment_method,
            monthly_charges,
            total_charges
        )
        VALUES
        (
            :customer_id,
            :tenure,
            :paperless_billing,
            :payment_method,
            :monthly_charges,
            :total_charges
        )
        ON DUPLICATE KEY UPDATE
            tenure = VALUES(tenure),
            paperless_billing = VALUES(paperless_billing),
            payment_method = VALUES(payment_method),
            monthly_charges = VALUES(monthly_charges),
            total_charges = VALUES(total_charges)
    """)

    # ========================================================
    # PROCESS EACH CUSTOMER
    # ========================================================

    with engine.begin() as connection:

        for _, customer_row in customers_df.iterrows():

            customer_id = customer_row["customer_id"]

            # ------------------------------------------------
            # Incoming customer values
            # ------------------------------------------------

            incoming_customer = {
                "customer_id": customer_id,
                "gender": normalize_value(
                    customer_row["gender"]
                ),
                "senior_citizen": normalize_value(
                    customer_row["senior_citizen"]
                ),
                "partner": normalize_value(
                    customer_row["partner"]
                ),
                "dependents": normalize_value(
                    customer_row["dependents"]
                )
            }

            # ------------------------------------------------
            # Find corresponding billing row
            # ------------------------------------------------

            billing_row = billing_df[
                billing_df["customer_id"] == customer_id
            ]

            if billing_row.empty:
                continue

            billing_row = billing_row.iloc[0]

            incoming_billing = {
                "customer_id": customer_id,
                "tenure": normalize_value(
                    billing_row["tenure"]
                ),
                "paperless_billing": normalize_paperless(
                    billing_row["paperless_billing"]
                ),
                "payment_method": normalize_value(
                    billing_row["payment_method"]
                ),
                "monthly_charges": normalize_value(
                    billing_row["monthly_charges"]
                ),
                "total_charges": normalize_value(
                    billing_row["total_charges"]
                )
            }

            # =================================================
            # CASE 1: NEW CUSTOMER
            # =================================================

            if customer_id not in existing_customers:

                connection.execute(
                    customer_upsert_sql,
                    incoming_customer
                )

                connection.execute(
                    billing_upsert_sql,
                    incoming_billing
                )

                rows_inserted += 1

                continue

            # =================================================
            # EXISTING CUSTOMER
            # =================================================

            existing_customer = existing_customers[
                customer_id
            ]

            existing_billing_row = existing_billing.get(
                customer_id
            )

            customer_changed = False
            billing_changed = False

            # =================================================
            # COMPARE CUSTOMER COLUMNS
            # =================================================

            customer_columns = [
                "gender",
                "senior_citizen",
                "partner",
                "dependents"
            ]

            for column in customer_columns:

                if not values_equal(
                    existing_customer[column],
                    incoming_customer[column]
                ):
                    customer_changed = True
                    break

            # =================================================
            # COMPARE BILLING COLUMNS
            # =================================================

            if existing_billing_row is None:

                billing_changed = True

            else:

                billing_columns = [
                    "tenure",
                    "paperless_billing",
                    "payment_method",
                    "monthly_charges",
                    "total_charges"
                ]

                for column in billing_columns:

                    existing_value = (
                        existing_billing_row[column]
                    )

                    incoming_value = (
                        incoming_billing[column]
                    )

                    # Special handling for paperless billing
                    if column == "paperless_billing":

                        existing_value = normalize_paperless(
                            existing_value
                        )

                        incoming_value = normalize_paperless(
                            incoming_value
                        )

                    if not values_equal(
                        existing_value,
                        incoming_value
                    ):
                        billing_changed = True
                        break

            # =================================================
            # CASE 2: UPDATED CUSTOMER
            # =================================================

            if customer_changed or billing_changed:

                if customer_changed:

                    connection.execute(
                        customer_upsert_sql,
                        incoming_customer
                    )

                if billing_changed:

                    connection.execute(
                        billing_upsert_sql,
                        incoming_billing
                    )

                rows_updated += 1

            # =================================================
            # CASE 3: UNCHANGED CUSTOMER
            # =================================================

            else:

                rows_unchanged += 1

    logger.info("Incremental load completed.")

    return (
        rows_inserted,
        rows_updated,
        rows_unchanged
    )


# ============================================================
# PIPELINE RUN LOG
# ============================================================

def log_pipeline_run(
    engine,
    file_name,
    rows_inserted,
    rows_updated,
    rows_unchanged
):

    with engine.begin() as connection:

        connection.execute(
            text("""
                INSERT INTO pipeline_run_log
                (
                    file_name,
                    rows_inserted,
                    rows_updated,
                    rows_unchanged,
                    run_timestamp
                )
                VALUES
                (
                    :file_name,
                    :rows_inserted,
                    :rows_updated,
                    :rows_unchanged,
                    :run_timestamp
                )
            """),
            {
                "file_name": file_name,
                "rows_inserted": rows_inserted,
                "rows_updated": rows_updated,
                "rows_unchanged": rows_unchanged,
                "run_timestamp": datetime.now()
            }
        )

    logger.info("Pipeline run logged successfully.")


# ============================================================
# VALIDATE CUSTOMERS
# ============================================================

def validate_customers(engine):

    with engine.connect() as connection:

        total_count = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM customers
            """)
        ).scalar()

        distinct_count = connection.execute(
            text("""
                SELECT COUNT(DISTINCT customer_id)
                FROM customers
            """)
        ).scalar()

    print("\n" + "=" * 60)
    print("CUSTOMER TABLE VALIDATION")
    print("=" * 60)

    print(f"Total customer rows   : {total_count}")
    print(f"Distinct customer IDs : {distinct_count}")

    if total_count == distinct_count:

        print("PASS: No duplicate customer_id values")

    else:

        print("ERROR: Duplicate customer_id values found")

        raise AssertionError(
            "Duplicate customer_id values found"
        )


# ============================================================
# VALIDATE BILLING
# ============================================================

def validate_billing(engine):

    with engine.connect() as connection:

        total_count = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM billing
            """)
        ).scalar()

        distinct_count = connection.execute(
            text("""
                SELECT COUNT(DISTINCT customer_id)
                FROM billing
            """)
        ).scalar()

        duplicate_result = connection.execute(
            text("""
                SELECT
                    customer_id,
                    COUNT(*) AS count
                FROM billing
                GROUP BY customer_id
                HAVING COUNT(*) > 1
                ORDER BY count DESC
                LIMIT 10
            """)
        )

        duplicates = duplicate_result.mappings().all()

    print("\n" + "=" * 60)
    print("BILLING TABLE VALIDATION")
    print("=" * 60)

    print(f"Total billing rows    : {total_count}")
    print(f"Distinct customer IDs : {distinct_count}")

    if total_count == distinct_count:

        print(
            "PASS: Billing table contains one "
            "billing record per customer"
        )

    else:

        print(
            "ERROR: Multiple billing records "
            "exist for some customers"
        )

        if duplicates:

            print("\nDuplicate billing records:")

            for row in duplicates:

                print(
                    f"  {row['customer_id']} "
                    f"-> {row['count']} records"
                )

        raise AssertionError(
            "Duplicate billing records found"
        )


# ============================================================
# DISPLAY LATEST RUN
# ============================================================

def show_latest_run(engine):

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT
    file_name,
    rows_inserted,
    rows_updated,
    rows_unchanged,
    run_timestamp
FROM pipeline_run_log
ORDER BY run_timestamp DESC
LIMIT 1
            """)
        )

        row = result.mappings().first()

    if row:

        print("\n" + "=" * 60)
        print("LATEST PIPELINE RUN")
        print("=" * 60)

        # print(f"Run ID       : {row['run_id']}")
        print(f"File         : {row['file_name']}")
        print(f"Inserted     : {row['rows_inserted']}")
        print(f"Updated      : {row['rows_updated']}")
        print(f"Unchanged    : {row['rows_unchanged']}")
        print(f"Timestamp    : {row['run_timestamp']}")


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 60)
    print("DE6 INCREMENTAL CUSTOMER PIPELINE")
    print("=" * 60)

    try:

        # ----------------------------------------------------
        # 1. READ AND CLEAN
        # ----------------------------------------------------

        df = read_customer_data()

        # ----------------------------------------------------
        # 2. INCREMENTAL LOAD
        # ----------------------------------------------------

        (
            rows_inserted,
            rows_updated,
            rows_unchanged
        ) = incremental_load(
            engine,
            df
        )

        # ----------------------------------------------------
        # 3. DISPLAY RESULT
        # ----------------------------------------------------

        print("\n" + "=" * 60)
        print("INCREMENTAL LOAD RESULT")
        print("=" * 60)

        print(f"Rows inserted  : {rows_inserted}")
        print(f"Rows updated   : {rows_updated}")
        print(f"Rows unchanged : {rows_unchanged}")

        # ----------------------------------------------------
        # 4. LOG RUN
        # ----------------------------------------------------

        log_pipeline_run(
            engine,
            CSV_PATH,
            rows_inserted,
            rows_updated,
            rows_unchanged
        )

        # ----------------------------------------------------
        # 5. VALIDATE CUSTOMERS
        # ----------------------------------------------------

        validate_customers(engine)

        # ----------------------------------------------------
        # 6. VALIDATE BILLING
        # ----------------------------------------------------

        validate_billing(engine)

        # ----------------------------------------------------
        # 7. SHOW LATEST RUN
        # ----------------------------------------------------

        show_latest_run(engine)

        print("\n" + "=" * 60)
        print("DE6 INCREMENTAL PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 60)

    except Exception as e:

        logger.error(
            f"DE6 FAILED: {e}"
        )

        raise


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()