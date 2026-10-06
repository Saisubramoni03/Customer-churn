"""
ML3 - Model Interpretation
Customer Churn Prediction Project

Purpose:
1. Load cleaned customer data from MySQL
2. Recreate the exact features used in ML2
3. Load the best ML2 model (Decision Tree)
4. Inspect feature importance
5. Identify top churn drivers
6. Score test-set customers
7. Display top 20 highest-risk customers
8. Compare ML high-risk customers with SQL rule-based high-risk customers
9. Print business interpretation
"""

import os
import sys
import logging
import joblib
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split


# ============================================================
# PATH SETUP
# ============================================================

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHASE5_PATH = os.path.join(PROJECT_ROOT, "phase5")

if PHASE5_PATH not in sys.path:
    sys.path.insert(0, PHASE5_PATH)


from db import engine # type: ignore


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "models",
    "tree_churn.pkl"
)

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "outputs"
)

CHART_PATH = os.path.join(
    OUTPUT_DIR,
    "top_feature_importance.png"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# LOAD DATA
# ============================================================

def load_customer_data():
    """
    Load the cleaned customer data required for ML3.
    """

    logger.info("Loading cleaned customer data from MySQL...")

    query = """
        SELECT
            customer_id,
            gender,
            senior_citizen,
            partner,
            dependents,
            tenure,
            phone_service,
            multiple_lines,
            internet_service,
            online_security,
            online_backup,
            device_protection,
            tech_support,
            streaming_tv,
            streaming_movies,
            contract,
            paperless_billing,
            payment_method,
            monthly_charges,
            total_charges,
            churn
        FROM cleaned_customers
    """

    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    logger.info("Rows loaded: %d", len(df))

    return df


# ============================================================
# BUILD DERIVED FEATURES
# ============================================================

def build_features(df):
    """
    Recreate the derived features used during ML2.

    IMPORTANT:
    The generated feature names and order MUST match ML2.
    """

    logger.info("Building derived ML features...")

    df = df.copy()

    # --------------------------------------------------------
    # Service count
    # --------------------------------------------------------

    service_columns = [
        "phone_service",
        "online_security",
        "online_backup",
        "device_protection",
        "tech_support",
        "streaming_tv",
        "streaming_movies"
    ]

    df["service_count"] = df[service_columns].sum(axis=1)

    # --------------------------------------------------------
    # High charge flag
    # --------------------------------------------------------

    df["high_charge_flag"] = (
        df["monthly_charges"] > 70
    ).astype(int)

    # --------------------------------------------------------
    # Long-term customer flag
    # --------------------------------------------------------

    df["is_long_term_customer"] = (
        df["tenure"] >= 24
    ).astype(int)

    # --------------------------------------------------------
    # Auto pay flag
    #
    # ML2's customer_ml_features table already contains
    # auto_pay_flag. Recreate it from payment_method here.
    # --------------------------------------------------------

    auto_pay_methods = [
        "Bank transfer (automatic)",
        "Credit card (automatic)"
    ]

    df["auto_pay_flag"] = (
        df["payment_method"].isin(auto_pay_methods)
    ).astype(int)

    # --------------------------------------------------------
    # Streaming bundle flag
    # --------------------------------------------------------

    df["has_streaming_bundle"] = (
        (df["streaming_tv"] == 1) &
        (df["streaming_movies"] == 1)
    ).astype(int)

    logger.info("Derived ML features created successfully.")

    return df


# ============================================================
# PREPARE X AND Y
# ============================================================

def prepare_ml_data(df):
    """
    Create X and y using exactly the same feature names
    and ordering used in ML2.
    """

    logger.info("Preparing feature matrix X and target y...")

    # --------------------------------------------------------
    # IMPORTANT:
    # ML2 used contract_type, NOT contract, as the prefix
    # for one-hot encoded columns.
    # --------------------------------------------------------

    df["contract_type"] = df["contract"]

    # --------------------------------------------------------
    # One-hot encoding
    # --------------------------------------------------------

    df = pd.get_dummies(
        df,
        columns=[
            "contract_type",
            "internet_service"
        ],
        drop_first=False
    )

    # --------------------------------------------------------
    # EXACT feature order from ML2
    # --------------------------------------------------------

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
        "internet_service_No"
    ]

    # --------------------------------------------------------
    # Make absolutely sure all expected columns exist
    # --------------------------------------------------------

    missing_columns = [
        col
        for col in feature_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing expected ML2 feature columns:\n"
            + "\n".join(f"  - {col}" for col in missing_columns)
        )

    X = df[feature_columns].copy()

    y = df["churn"].copy()

    logger.info("X shape: %s", X.shape)
    logger.info("y shape: %s", y.shape)

    return df, X, y, feature_columns


# ============================================================
# LOAD MODEL
# ============================================================

def load_model():
    """
    Load the Decision Tree model selected in ML2.
    """

    logger.info("Loading Decision Tree model...")

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model not found: {MODEL_PATH}"
        )

    model = joblib.load(MODEL_PATH)

    logger.info("Decision Tree model loaded successfully.")

    return model


# ============================================================
# CHECK MODEL FEATURES
# ============================================================

def validate_features(model, feature_columns):
    """
    Verify that ML3 features exactly match ML2 features.
    """

    if hasattr(model, "feature_names_in_"):

        model_features = list(model.feature_names_in_)

        if model_features != feature_columns:

            print("\nERROR: Feature mismatch.\n")

            print("Model features:")
            for feature in model_features:
                print(f"  - {feature}")

            print("\nCurrent features:")
            for feature in feature_columns:
                print(f"  - {feature}")

            raise ValueError(
                "The features generated in ML3 do not exactly "
                "match the features used to train the ML2 model."
            )

    else:

        if model.n_features_in_ != len(feature_columns):
            raise ValueError(
                f"Model expects {model.n_features_in_} features, "
                f"but ML3 generated {len(feature_columns)}."
            )

    logger.info("Feature validation passed.")


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

def analyze_feature_importance(model, feature_columns):

    print("\n" + "=" * 70)
    print("DECISION TREE FEATURE IMPORTANCE")
    print("=" * 70)

    importances = pd.Series(
        model.feature_importances_,
        index=feature_columns
    )

    importances = importances.sort_values(
        ascending=False
    )

    print("\nALL FEATURE IMPORTANCES:\n")

    for feature, importance in importances.items():
        print(
            f"{feature:<40} {importance:.6f}"
        )

    # --------------------------------------------------------
    # Top 10
    # --------------------------------------------------------

    top_10 = importances.head(10)

    print("\n" + "=" * 70)
    print("TOP 10 FEATURES")
    print("=" * 70)

    for rank, (feature, importance) in enumerate(
        top_10.items(),
        start=1
    ):
        print(
            f"{rank:2}. {feature:<40} "
            f"{importance:.6f}"
        )

    # --------------------------------------------------------
    # Top 3
    # --------------------------------------------------------

    top_3 = importances.head(3)

    print("\n" + "=" * 70)
    print("TOP 3 CHURN-ASSOCIATED FEATURES")
    print("=" * 70)

    for rank, (feature, importance) in enumerate(
        top_3.items(),
        start=1
    ):
        print(
            f"{rank}. {feature} "
            f"(importance={importance:.6f})"
        )

    # --------------------------------------------------------
    # Plot
    # --------------------------------------------------------

    plt.figure(figsize=(10, 6))

    top_10.sort_values().plot(
        kind="barh"
    )

    plt.title(
        "Top 10 Feature Importances - Decision Tree"
    )

    plt.xlabel("Feature Importance")
    plt.ylabel("Feature")

    plt.tight_layout()

    plt.savefig(
        CHART_PATH,
        dpi=150
    )

    plt.close()

    print(
        f"\nINFO: Feature importance chart saved to:\n"
        f"{CHART_PATH}"
    )

    return importances


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

def create_test_set(X, y, df):

    print("\n" + "=" * 70)
    print("CREATING TEST SET")
    print("=" * 70)

    (
        X_train,
        X_test,
        y_train,
        y_test,
        df_train,
        df_test
    ) = train_test_split(
        X,
        y,
        df,
        test_size=0.2,
        stratify=y,
        random_state=42
    )

    print(f"\nTraining rows : {len(X_train)}")
    print(f"Testing rows  : {len(X_test)}")

    return (
        X_train,
        X_test,
        y_train,
        y_test,
        df_train,
        df_test
    )


# ============================================================
# SCORE HIGH-RISK CUSTOMERS
# ============================================================

def find_high_risk_customers(
    model,
    X_test,
    df_test
):

    print("\n" + "=" * 70)
    print("TOP 20 HIGHEST-RISK CUSTOMERS")
    print("=" * 70)

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

    results = pd.DataFrame({
        "customer_id": df_test["customer_id"].values,
        "actual_churn": df_test["churn"].values,
        "churn_probability": probabilities
    })

    results = results.sort_values(
        "churn_probability",
        ascending=False
    ).reset_index(drop=True)

    top_20 = results.head(20).copy()

    top_20["risk_score"] = (
        top_20["churn_probability"] * 100
    ).round(2)

    print(
        "\n"
        + f"{'Rank':<6}"
        + f"{'Customer ID':<18}"
        + f"{'Actual':<10}"
        + f"{'Risk Score':<12}"
        + "Churn Probability"
    )

    print("-" * 70)

    for index, row in top_20.iterrows():

        print(
            f"{index + 1:<6}"
            f"{row['customer_id']:<18}"
            f"{row['actual_churn']:<10}"
            f"{row['risk_score']:<12}"
            f"{row['churn_probability']:.4f}"
        )

    # --------------------------------------------------------
    # Save results
    # --------------------------------------------------------

    risk_path = os.path.join(
        OUTPUT_DIR,
        "top_20_high_risk_customers.csv"
    )

    top_20.to_csv(
        risk_path,
        index=False
    )

    print(
        f"\nINFO: High-risk customer list saved to:\n"
        f"{risk_path}"
    )

    return top_20, results


# ============================================================
# SQL RULE-BASED HIGH-RISK COMPARISON
# ============================================================

def compare_with_sql_high_risk(top_20):

    print("\n" + "=" * 70)
    print("ML HIGH-RISK VS SQL RULE-BASED HIGH-RISK")
    print("=" * 70)

    try:

        query = """
            SELECT customer_id
            FROM v_high_risk_customers
        """

        with engine.connect() as conn:
            sql_df = pd.read_sql(
                query,
                conn
            )

        sql_ids = set(
            sql_df["customer_id"]
        )

        ml_ids = set(
            top_20["customer_id"]
        )

        overlap = ml_ids.intersection(
            sql_ids
        )

        print(
            f"\nSQL high-risk customers : "
            f"{len(sql_ids)}"
        )

        print(
            f"ML top-20 customers      : "
            f"{len(ml_ids)}"
        )

        print(
            f"Overlap                   : "
            f"{len(overlap)}"
        )

        if len(overlap) > 0:

            print("\nCustomers appearing in BOTH lists:")

            for customer_id in sorted(overlap):
                print(
                    f"  - {customer_id}"
                )

        else:

            print(
                "\nNo overlap found between "
                "the ML top-20 and SQL rule-based list."
            )

        overlap_percentage = (
            len(overlap) / len(ml_ids) * 100
        )

        print(
            f"\nTop-20 ML overlap percentage: "
            f"{overlap_percentage:.2f}%"
        )

        return overlap

    except Exception as e:

        print(
            "\nWARNING: Could not compare with "
            "SQL high-risk list."
        )

        print(
            f"Reason: {e}"
        )

        return set()


# ============================================================
# BUSINESS INTERPRETATION
# ============================================================

def print_business_interpretation(
    importances,
    top_20
):

    print("\n" + "=" * 70)
    print("BUSINESS INTERPRETATION")
    print("=" * 70)

    top_features = list(
        importances.head(3).index
    )

    print(
        "\nCustomers most likely to churn are those whose "
        "behaviour and account characteristics align with "
        "the strongest predictive features identified by "
        "the Decision Tree."
    )

    print(
        f"The three most influential features are "
        f"{top_features[0]}, {top_features[1]}, "
        f"and {top_features[2]}."
    )

    print(
        "Retention teams should pay particular attention "
        "to customers showing combinations of these "
        "high-risk characteristics."
    )

    print(
        "The model's churn probability provides a way to "
        "prioritize customers instead of treating every "
        "customer as equally likely to leave."
    )

    print(
        "The highest-risk customers can therefore be "
        "targeted proactively with retention offers, "
        "service support, or personalized interventions."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 70)
    print("ML3 MODEL INTERPRETATION")
    print("=" * 70)

    try:

        # ----------------------------------------------------
        # 1. Load data
        # ----------------------------------------------------

        df = load_customer_data()

        # ----------------------------------------------------
        # 2. Build derived features
        # ----------------------------------------------------

        df = build_features(df)

        # ----------------------------------------------------
        # 3. Prepare X and y
        # ----------------------------------------------------

        df, X, y, feature_columns = prepare_ml_data(
            df
        )

        # ----------------------------------------------------
        # 4. Load best model
        # ----------------------------------------------------

        model = load_model()

        # ----------------------------------------------------
        # 5. Validate feature compatibility
        # ----------------------------------------------------

        validate_features(
            model,
            feature_columns
        )

        # ----------------------------------------------------
        # 6. Feature importance
        # ----------------------------------------------------

        importances = analyze_feature_importance(
            model,
            feature_columns
        )

        # ----------------------------------------------------
        # 7. Create same test split as ML2
        # ----------------------------------------------------

        (
            X_train,
            X_test,
            y_train,
            y_test,
            df_train,
            df_test
        ) = create_test_set(
            X,
            y,
            df
        )

        # ----------------------------------------------------
        # 8. Score customers
        # ----------------------------------------------------

        top_20, all_results = find_high_risk_customers(
            model,
            X_test,
            df_test
        )

        # ----------------------------------------------------
        # 9. Compare with SQL6
        # ----------------------------------------------------

        overlap = compare_with_sql_high_risk(
            top_20
        )

        # ----------------------------------------------------
        # 10. Business interpretation
        # ----------------------------------------------------

        print_business_interpretation(
            importances,
            top_20
        )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        print("\n" + "=" * 70)
        print("ML3 COMPLETED SUCCESSFULLY")
        print("=" * 70)

        print(
            "\nOutputs:"
        )

        print(
            f"  Feature chart : {CHART_PATH}"
        )

        print(
            f"  High-risk CSV : "
            f"{os.path.join(OUTPUT_DIR, 'top_20_high_risk_customers.csv')}"
        )

        print(
            f"  SQL/ML overlap: {len(overlap)} customers"
        )

    except Exception as e:

        logger.error(
            "ML3 FAILED: %s",
            e
        )

        raise


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()