import os
import sys
import logging

import pandas as pd
import joblib

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)


# ============================================================
# CONFIGURATION
# ============================================================

RANDOM_STATE = 42
TEST_SIZE = 0.2

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
# PATHS
# ============================================================

MODELS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "models"
)

LOGISTIC_MODEL_PATH = os.path.join(
    MODELS_DIR,
    "logistic_churn.pkl"
)

TREE_MODEL_PATH = os.path.join(
    MODELS_DIR,
    "tree_churn.pkl"
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# LOAD ML DATA
# ============================================================

def load_ml_data():

    logger.info(
        "Loading customer_ml_features from MySQL..."
    )

    query = """
        SELECT
            customer_id,
            tenure,
            monthly_charges,
            total_charges,
            service_count,
            high_charge_flag,
            is_long_term_customer,
            auto_pay_flag,
            has_streaming_bundle,
            contract_type,
            internet_service,
            churn
        FROM customer_ml_features
    """

    df = pd.read_sql(
        query,
        engine
    )

    logger.info(
        f"Rows loaded: {len(df)}"
    )

    return df


# ============================================================
# PREPARE X AND Y
# ============================================================

def prepare_data(df):

    logger.info(
        "Preparing feature matrix X and target y..."
    )

    # Target
    y = df["churn"].astype(int)

    # Remove identifier and target
    X = df.drop(
        columns=[
            "customer_id",
            "churn"
        ]
    )

    # One-hot encode categorical columns
    X = pd.get_dummies(
        X,
        columns=[
            "contract_type",
            "internet_service"
        ],
        drop_first=False,
        dtype=int
    )

    logger.info(
        f"X shape: {X.shape}"
    )

    logger.info(
        f"y shape: {y.shape}"
    )

    return X, y


# ============================================================
# TRAIN TEST SPLIT
# ============================================================

def split_data(X, y):

    logger.info(
        "Splitting data into training and testing sets..."
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        stratify=y,
        random_state=RANDOM_STATE
    )

    print("\n" + "=" * 70)
    print("TRAIN / TEST SPLIT")
    print("=" * 70)

    print(f"Training rows : {len(X_train)}")
    print(f"Testing rows  : {len(X_test)}")

    print("\nTraining class balance:")
    print(y_train.value_counts(normalize=True))

    print("\nTesting class balance:")
    print(y_test.value_counts(normalize=True))

    return (
        X_train,
        X_test,
        y_train,
        y_test
    )


# ============================================================
# TRAIN LOGISTIC REGRESSION
# ============================================================

def train_logistic(X_train, y_train):

    logger.info(
        "Training Logistic Regression..."
    )

    model = LogisticRegression(
        max_iter=1000
    )

    model.fit(
        X_train,
        y_train
    )

    logger.info(
        "Logistic Regression training completed."
    )

    return model


# ============================================================
# TRAIN DECISION TREE
# ============================================================

def train_tree(X_train, y_train):

    logger.info(
        "Training Decision Tree..."
    )

    model = DecisionTreeClassifier(
        max_depth=5,
        random_state=RANDOM_STATE
    )

    model.fit(
        X_train,
        y_train
    )

    logger.info(
        "Decision Tree training completed."
    )

    return model


# ============================================================
# EVALUATE MODEL
# ============================================================

def evaluate_model(
    model,
    model_name,
    X_test,
    y_test,
    X,
    y
):

    print("\n" + "=" * 70)
    print(model_name.upper())
    print("=" * 70)

    # --------------------------------------------------------
    # Predictions
    # --------------------------------------------------------

    y_pred = model.predict(
        X_test
    )

    # --------------------------------------------------------
    # Classification report
    # --------------------------------------------------------

    print("\nCLASSIFICATION REPORT")
    print(
        classification_report(
            y_test,
            y_pred,
            target_names=[
                "Active",
                "Churned"
            ]
        )
    )

    # --------------------------------------------------------
    # Confusion matrix
    # --------------------------------------------------------

    cm = confusion_matrix(
        y_test,
        y_pred
    )

    print("CONFUSION MATRIX")
    print(cm)

    # --------------------------------------------------------
    # Test metrics
    # --------------------------------------------------------

    accuracy = accuracy_score(
        y_test,
        y_pred
    )

    precision = precision_score(
        y_test,
        y_pred,
        zero_division=0
    )

    recall = recall_score(
        y_test,
        y_pred,
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        y_pred,
        zero_division=0
    )

    # --------------------------------------------------------
    # 5-fold cross-validation F1
    # --------------------------------------------------------

    cv_scores = cross_val_score(
        model,
        X,
        y,
        cv=5,
        scoring="f1"
    )

    cv_f1 = cv_scores.mean()

    print("\n5-FOLD CROSS-VALIDATION F1")
    print(
        f"Scores : {cv_scores}"
    )

    print(
        f"Mean CV F1 : {cv_f1:.4f}"
    )

    return {
        "Model": model_name,
        "Accuracy": accuracy,
        "Precision (Churned)": precision,
        "Recall (Churned)": recall,
        "F1 (Churned)": f1,
        "CV F1": cv_f1
    }


# ============================================================
# SAVE MODELS
# ============================================================

def save_models(
    logistic_model,
    tree_model
):

    os.makedirs(
        MODELS_DIR,
        exist_ok=True
    )

    joblib.dump(
        logistic_model,
        LOGISTIC_MODEL_PATH
    )

    joblib.dump(
        tree_model,
        TREE_MODEL_PATH
    )

    logger.info(
        f"Logistic model saved: {LOGISTIC_MODEL_PATH}"
    )

    logger.info(
        f"Decision Tree model saved: {TREE_MODEL_PATH}"
    )


# ============================================================
# MODEL COMPARISON
# ============================================================

def compare_models(results):

    comparison = pd.DataFrame(
        results
    )

    print("\n" + "=" * 70)
    print("MODEL COMPARISON")
    print("=" * 70)

    print(
        comparison.to_string(
            index=False,
            formatters={
                "Accuracy": "{:.4f}".format,
                "Precision (Churned)": "{:.4f}".format,
                "Recall (Churned)": "{:.4f}".format,
                "F1 (Churned)": "{:.4f}".format,
                "CV F1": "{:.4f}".format
            }
        )
    )

    # --------------------------------------------------------
    # Select based on F1 for Churned class
    # --------------------------------------------------------

    best_row = comparison.loc[
        comparison["F1 (Churned)"].idxmax()
    ]

    print("\n" + "=" * 70)
    print("MODEL SELECTION")
    print("=" * 70)

    print(
        f"Selected model: {best_row['Model']}"
    )

    print(
        f"Churned F1: "
        f"{best_row['F1 (Churned)']:.4f}"
    )

    print(
        "\nReason:"
    )

    print(
        "The model with the higher F1 score for "
        "the Churned class provides the better balance "
        "between identifying churners and avoiding "
        "incorrect churn predictions."
    )

    print(
        "\nRecall is also important because a false negative "
        "means a customer likely to churn was missed."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 70)
    print("ML2 CUSTOMER CHURN MODEL TRAINING")
    print("=" * 70)

    try:

        # ----------------------------------------------------
        # 1. Load data
        # ----------------------------------------------------

        df = load_ml_data()

        # ----------------------------------------------------
        # 2. Prepare X and y
        # ----------------------------------------------------

        X, y = prepare_data(df)

        # ----------------------------------------------------
        # 3. Split
        # ----------------------------------------------------

        (
            X_train,
            X_test,
            y_train,
            y_test
        ) = split_data(
            X,
            y
        )

        # ----------------------------------------------------
        # 4. Train models
        # ----------------------------------------------------

        logistic_model = train_logistic(
            X_train,
            y_train
        )

        tree_model = train_tree(
            X_train,
            y_train
        )

        # ----------------------------------------------------
        # 5. Evaluate Logistic Regression
        # ----------------------------------------------------

        logistic_results = evaluate_model(
            logistic_model,
            "Logistic Regression",
            X_test,
            y_test,
            X,
            y
        )

        # ----------------------------------------------------
        # 6. Evaluate Decision Tree
        # ----------------------------------------------------

        tree_results = evaluate_model(
            tree_model,
            "Decision Tree",
            X_test,
            y_test,
            X,
            y
        )

        # ----------------------------------------------------
        # 7. Comparison
        # ----------------------------------------------------

        compare_models([
            logistic_results,
            tree_results
        ])

        # ----------------------------------------------------
        # 8. Save models
        # ----------------------------------------------------

        save_models(
            logistic_model,
            tree_model
        )

        print("\n" + "=" * 70)
        print("ML2 COMPLETED SUCCESSFULLY")
        print("=" * 70)

        print(
            "\nModels saved in:"
        )

        print(
            f"  {LOGISTIC_MODEL_PATH}"
        )

        print(
            f"  {TREE_MODEL_PATH}"
        )

    except Exception as e:

        logger.error(
            f"ML2 FAILED: {e}"
        )

        raise


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()