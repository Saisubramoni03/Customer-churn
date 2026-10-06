import os
import joblib
import pandas as pd
import sys

# Add parent directory to path to import database module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import engine

# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "tree_churn.pkl")

# ============================================================
# LOAD MODEL ONCE AT MODULE LEVEL
# ============================================================

print("INFO: Loading Decision Tree churn model...")

model = joblib.load(MODEL_PATH)

print("INFO: Decision Tree model loaded successfully.")


# ============================================================
# TRAINING FEATURE COLUMNS
# Must match exactly what the model was trained with
# ============================================================

FEATURE_COLUMNS = [
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

print(f"INFO: Using {len(FEATURE_COLUMNS)} feature columns for model prediction")

# ============================================================
# OPTIONAL: Get customer data from database for enrichment
# ============================================================

def get_customer_from_db(customer_id):
    """
    Optional: Get customer data from database for additional context.
    """
    try:
        query = f"""
        SELECT *
        FROM customers
        WHERE customer_id = '{customer_id}'
        LIMIT 1
        """
        df = pd.read_sql(query, engine)
        if not df.empty:
            return df.iloc[0].to_dict()
        return None
    except Exception as e:
        print(f"WARNING: Could not fetch customer data: {str(e)}")
        return None


# ============================================================
# PREPROCESS INPUT
# ============================================================

def preprocess_input(
    tenure,
    monthly_charges,
    contract_type,
    service_count
):
    """
    Convert API input into the exact feature format
    used during ML2 model training.
    Creates realistic feature variations based on input parameters.
    """

    # --------------------------------------------------------
    # Numeric features and derived features
    # --------------------------------------------------------

    total_charges = tenure * monthly_charges

    # High charge flag: > $70 monthly indicates higher risk
    high_charge_flag = 1 if monthly_charges > 70 else 0

    # Long-term customer: >= 24 months shows commitment
    is_long_term_customer = 1 if tenure >= 24 else 0

    # Streaming bundle: correlate with service_count
    # If service_count >= 3, likely has streaming
    has_streaming_bundle = 1 if service_count >= 3 else 0

    # Auto pay: correlate with tenure and charges
    # Longer tenure and lower charges suggest auto-pay
    auto_pay_flag = 1 if (tenure >= 12 and monthly_charges < 80) else 0

    # --------------------------------------------------------
    # Contract type one-hot encoding
    # Month-to-month has highest churn risk
    # --------------------------------------------------------

    contract_type_month_to_month = 1 if contract_type == "Month-to-month" else 0
    contract_type_one_year = 1 if contract_type == "One year" else 0
    contract_type_two_year = 1 if contract_type == "Two year" else 0

    # --------------------------------------------------------
    # Internet service one-hot encoding
    # Vary based on monthly charges
    # High charges = Fiber optic, Low charges = DSL, Very low = No
    # --------------------------------------------------------

    if monthly_charges > 80:
        internet_service_dsl = 0
        internet_service_fiber = 1
        internet_service_no = 0
    elif monthly_charges < 30:
        internet_service_dsl = 0
        internet_service_fiber = 0
        internet_service_no = 1
    else:
        internet_service_dsl = 1
        internet_service_fiber = 0
        internet_service_no = 0

    # --------------------------------------------------------
    # Create single-row DataFrame
    # --------------------------------------------------------

    data = {
        "tenure": [tenure],
        "monthly_charges": [monthly_charges],
        "total_charges": [total_charges],
        "service_count": [service_count],
        "high_charge_flag": [high_charge_flag],
        "is_long_term_customer": [is_long_term_customer],
        "auto_pay_flag": [auto_pay_flag],
        "has_streaming_bundle": [has_streaming_bundle],

        "contract_type_Month-to-month": [
            contract_type_month_to_month
        ],
        "contract_type_One year": [
            contract_type_one_year
        ],
        "contract_type_Two year": [
            contract_type_two_year
        ],

        "internet_service_DSL": [
            internet_service_dsl
        ],
        "internet_service_Fiber optic": [
            internet_service_fiber
        ],
        "internet_service_No": [
            internet_service_no
        ],
    }

    df = pd.DataFrame(data)

    # Make absolutely sure column order matches training
    df = df[FEATURE_COLUMNS]

    return df


# ============================================================
# PREDICTION FUNCTION
# ============================================================

def predict_churn(
    tenure,
    monthly_charges,
    contract_type,
    service_count
):
    """
    Predict customer churn probability using database-trained model.
    """

    # Preprocess input
    X = preprocess_input(
        tenure=tenure,
        monthly_charges=monthly_charges,
        contract_type=contract_type,
        service_count=service_count
    )

    # Prediction
    prediction = int(model.predict(X)[0])

    # Probability of churn
    churn_probability = float(
        model.predict_proba(X)[0][1]
    )

    # Convert probability to percentage
    risk_score = round(churn_probability * 100, 2)

    # Prediction label
    if prediction == 1:
        prediction_text = "Likely to churn"
        confidence = round(
                float(min(model.predict_proba(X)[0])) * 100,
                2
            )
    else:
        prediction_text = "Unlikely to churn"
        confidence = round(
                float(max(model.predict_proba(X)[0])) * 100,
                2
            )

    # Confidence (max probability of either class, converted to percentage)
    # confidence = round(
    #     float(max(model.predict_proba(X)[0])) * 100,
    #     2
    # )

    return {
        "risk_score": risk_score,
        "prediction": prediction_text,
        "confidence": confidence
    }