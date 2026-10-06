
import os
import sys
from datetime import datetime

import pandas as pd
from sqlalchemy import text

# ------------------------------------------------------------------
# Allow importing db.py from phase5
# ------------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHASE5_DIR = os.path.join(PROJECT_ROOT, "phase5")

if PHASE5_DIR not in sys.path:
    sys.path.insert(0, PHASE5_DIR)

from db import engine # type: ignore

from predict import predict_churn


# ==================================================================
# CONFIGURATION
# ==================================================================

OUTPUT_TABLE = "customer_risk_table"


# ==================================================================
# LOAD CUSTOMER DATA
# ==================================================================

def load_customer_data():
    print("INFO: Loading customer data from MySQL...")

    query = """
        SELECT
            customer_id,
            tenure,
            internet_service,
            contract,
            monthly_charges,
            total_charges,
            churn
        FROM cleaned_customers
    """

    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    print(f"INFO: Rows loaded: {len(df)}")

    return df


# ==================================================================
# BUILD DERIVED FEATURES
# ==================================================================

def build_features(df):
    print("INFO: Building features required by ML2 model...")

    df = df.copy()

    # --------------------------------------------------------------
    # service_count
    #
    # Count the services used by the customer.
    # --------------------------------------------------------------

    service_columns = [
        "phone_service",
        "online_security",
        "online_backup",
        "device_protection",
        "tech_support",
        "streaming_tv",
        "streaming_movies",
    ]

    # These columns are not selected in the first query,
    # so service_count will be calculated using the available
    # customer data in a second query.
    return df


# ==================================================================
# LOAD COMPLETE DATA REQUIRED FOR ML FEATURES
# ==================================================================

def load_model_input_data():
    print("INFO: Loading complete customer data for batch scoring...")

    query = """
        SELECT
            customer_id,
            tenure,
            internet_service,
            contract,
            monthly_charges,
            total_charges,
            phone_service,
            online_security,
            online_backup,
            device_protection,
            tech_support,
            streaming_tv,
            streaming_movies,
            churn
        FROM cleaned_customers
    """

    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)

    print(f"INFO: Complete customer rows loaded: {len(df)}")

    return df


# ==================================================================
# CREATE ML2 FEATURES
# ==================================================================

def prepare_model_features(df):

    print("INFO: Preparing ML2-compatible features...")

    df = df.copy()

    # --------------------------------------------------------------
    # Service count
    # --------------------------------------------------------------

    service_columns = [
        "phone_service",
        "online_security",
        "online_backup",
        "device_protection",
        "tech_support",
        "streaming_tv",
        "streaming_movies",
    ]

    df["service_count"] = df[service_columns].sum(axis=1)

    # --------------------------------------------------------------
    # Derived features
    # --------------------------------------------------------------

    df["high_charge_flag"] = (
        df["monthly_charges"] > 70
    ).astype(int)

    df["is_long_term_customer"] = (
        df["tenure"] >= 24
    ).astype(int)

    # These were not part of the ML4 input.
    # For consistency with predict.py, use 0.
    df["auto_pay_flag"] = 0
    df["has_streaming_bundle"] = (
        (
            (df["streaming_tv"] == 1)
            | (df["streaming_movies"] == 1)
        )
    ).astype(int)

    # --------------------------------------------------------------
    # Rename contract to contract_type
    # --------------------------------------------------------------

    df["contract_type"] = df["contract"]

    # --------------------------------------------------------------
    # One-hot encode contract
    # --------------------------------------------------------------

    contract_dummies = pd.get_dummies(
        df["contract_type"],
        prefix="contract_type",
        dtype=int
    )

    # Guarantee all three expected columns exist
    expected_contract_columns = [
        "contract_type_Month-to-month",
        "contract_type_One year",
        "contract_type_Two year",
    ]

    for column in expected_contract_columns:
        if column not in contract_dummies.columns:
            contract_dummies[column] = 0

    contract_dummies = contract_dummies[
        expected_contract_columns
    ]

    # --------------------------------------------------------------
    # One-hot encode internet service
    # --------------------------------------------------------------

    internet_dummies = pd.get_dummies(
        df["internet_service"],
        prefix="internet_service",
        dtype=int
    )

    expected_internet_columns = [
        "internet_service_DSL",
        "internet_service_Fiber optic",
        "internet_service_No",
    ]

    for column in expected_internet_columns:
        if column not in internet_dummies.columns:
            internet_dummies[column] = 0

    internet_dummies = internet_dummies[
        expected_internet_columns
    ]

    # --------------------------------------------------------------
    # Combine everything
    # --------------------------------------------------------------

    model_df = pd.DataFrame()

    model_df["tenure"] = df["tenure"]
    model_df["monthly_charges"] = df["monthly_charges"]
    model_df["total_charges"] = df["total_charges"]
    model_df["service_count"] = df["service_count"]
    model_df["high_charge_flag"] = df["high_charge_flag"]
    model_df["is_long_term_customer"] = df[
        "is_long_term_customer"
    ]
    model_df["auto_pay_flag"] = df["auto_pay_flag"]
    model_df["has_streaming_bundle"] = df[
        "has_streaming_bundle"
    ]

    model_df = pd.concat(
        [
            model_df,
            contract_dummies,
            internet_dummies,
        ],
        axis=1
    )

    # --------------------------------------------------------------
    # Exact ML2 feature order
    # --------------------------------------------------------------

    feature_columns = [
        "tenure",
        "monthly_charges",
        "total_charges",
        "service_count",
        "high_charge_flag",
        "is_long_term_customer",
        "auto_pay_flag",
        "has_streaming_bundle",
        "contract_type_Month-to-month",
        "contract_type_One year",
        "contract_type_Two year",
        "internet_service_DSL",
        "internet_service_Fiber optic",
        "internet_service_No",
    ]

    model_df = model_df[feature_columns]

    print(
        f"INFO: Model feature matrix created: "
        f"{model_df.shape}"
    )

    return model_df


# ==================================================================
# BATCH SCORING
# ==================================================================

def batch_score(customers, X):

    print("INFO: Starting batch scoring...")

    results = customers[
        ["customer_id", "churn"]
    ].copy()

    # --------------------------------------------------------------
    # Apply the same prediction function used by ML4
    # --------------------------------------------------------------

    predictions = customers.apply(
        lambda row: predict_churn(
            tenure=int(row["tenure"]),
            monthly_charges=float(row["monthly_charges"]),
            contract_type=row["contract"],
            service_count=int(row["service_count"])
        ),
        axis=1
    )

    results["risk_score"] = predictions.apply(
        lambda x: x["risk_score"]
    )

    results["prediction"] = predictions.apply(
        lambda x: x["prediction"]
    )

    results["confidence"] = predictions.apply(
        lambda x: x["confidence"]
    )

    results["scoring_date"] = datetime.today().strftime(
        "%Y-%m-%d"
    )

    print("INFO: Batch scoring completed.")

    return results


# ==================================================================
# SAVE CUSTOMER RISK TABLE
# ==================================================================

def save_risk_table(results):

    print(
        f"INFO: Saving {len(results)} risk records "
        f"to {OUTPUT_TABLE}..."
    )

    output = results[
        [
            "customer_id",
            "risk_score",
            "prediction",
            "confidence",
            "scoring_date",
        ]
    ].copy()

    output.to_sql(
        OUTPUT_TABLE,
        engine,
        if_exists="replace",
        index=False
    )

    print(
        f"INFO: {OUTPUT_TABLE} created successfully."
    )


# ==================================================================
# PRINT SUMMARY
# ==================================================================

def print_summary(results):

    print()
    print("=" * 70)
    print("ML5 BATCH SCORING SUMMARY")
    print("=" * 70)

    prediction_counts = results["prediction"].value_counts()

    likely_to_churn = prediction_counts.get(
        "Likely to churn",
        0
    )

    unlikely_to_churn = prediction_counts.get(
        "Unlikely to churn",
        0
    )

    total = len(results)

    churn_percentage = (
        likely_to_churn / total * 100
        if total > 0
        else 0
    )

    print(f"Total customers       : {total}")
    print(
        f"Likely to churn       : "
        f"{likely_to_churn}"
    )
    print(
        f"Unlikely to churn     : "
        f"{unlikely_to_churn}"
    )
    print(
        f"Predicted churn rate  : "
        f"{churn_percentage:.2f}%"
    )

    print()
    print(
        "Training churn rate   : 26.54%"
    )

    print()


# ==================================================================
# TOP 10 HIGH-RISK CUSTOMERS
# ==================================================================

def print_top_risk_customers(results):

    print("=" * 70)
    print("TOP 10 HIGHEST-RISK CUSTOMERS")
    print("=" * 70)

    top10 = results.sort_values(
        by="risk_score",
        ascending=False
    ).head(10)

    print(
        f"{'Rank':<6}"
        f"{'Customer ID':<18}"
        f"{'Risk Score':<15}"
        f"{'Prediction':<20}"
    )

    print("-" * 70)

    for rank, (_, row) in enumerate(
        top10.iterrows(),
        start=1
    ):

        print(
            f"{rank:<6}"
            f"{row['customer_id']:<18}"
            f"{row['risk_score']:<15.2f}"
            f"{row['prediction']:<20}"
        )


# ==================================================================
# MAIN
# ==================================================================

def main():

    print()
    print("=" * 70)
    print("ML5 CUSTOMER BATCH SCORING")
    print("=" * 70)

    try:

        # Load data
        customers = load_model_input_data()

        # Prepare features
        X = prepare_model_features(customers)

        # Store service_count so batch_score can use it
        customers["service_count"] = (
            customers[
                [
                    "phone_service",
                    "online_security",
                    "online_backup",
                    "device_protection",
                    "tech_support",
                    "streaming_tv",
                    "streaming_movies",
                ]
            ].sum(axis=1)
        )

        # Batch prediction
        results = batch_score(
            customers,
            X
        )

        # Save results
        save_risk_table(results)

        # Summary
        print_summary(results)

        # Top 10
        print_top_risk_customers(results)

        print()
        print("=" * 70)
        print("ML5 BATCH SCORING COMPLETED SUCCESSFULLY")
        print("=" * 70)

    except Exception as e:

        print()
        print(
            f"ERROR: ML5 FAILED: {e}"
        )

        raise


if __name__ == "__main__":
    main()

