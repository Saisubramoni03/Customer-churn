import os
import sys
import json
import logging

import pandas as pd


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


from customer_cleaner import CustomerCleaner # type: ignore


# ============================================================
# CONFIGURATION
# ============================================================

CSV_PATH = "data/raw/customer_churn.csv"

REPORT_PATH = "data/logs/quality_report.json"


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)


# ============================================================
# 1. NULL RATE CHECK
# ============================================================

def check_null_rate(df, col, threshold):
    """
    Check whether the null percentage of a column
    is within the allowed threshold.
    """

    null_count = df[col].isna().sum()

    null_rate = (
        null_count / len(df) * 100
        if len(df) > 0
        else 0
    )

    passed = null_rate <= threshold

    return {
        "check_name": f"Null rate - {col}",
        "status": "PASS" if passed else "FAIL",
        "value_found": f"{null_rate:.2f}%",
        "threshold": f"<= {threshold:.2f}%",
        "severity": "CRITICAL"
    }


# ============================================================
# 2. VALUE RANGE CHECK
# ============================================================

def check_value_range(df, col, min_value=None, max_value=None):
    """
    Check whether all values in a column fall
    within the specified range.
    """

    values = pd.to_numeric(
        df[col],
        errors="coerce"
    )

    actual_min = values.min()
    actual_max = values.max()

    passed = True

    if min_value is not None:
        if actual_min < min_value:
            passed = False

    if max_value is not None:
        if actual_max > max_value:
            passed = False

    if min_value is not None and max_value is not None:
        threshold = f"{min_value} - {max_value}"
    elif min_value is not None:
        threshold = f">= {min_value}"
    else:
        threshold = f"<= {max_value}"

    return {
        "check_name": f"Value range - {col}",
        "status": "PASS" if passed else "FAIL",
        "value_found": f"min={actual_min}, max={actual_max}",
        "threshold": threshold,
        "severity": "CRITICAL"
    }


# ============================================================
# 3. ALLOWED VALUES CHECK
# ============================================================

def check_allowed_values(df, col, allowed_set):
    """
    Check whether a column contains only allowed values.
    """

    actual_values = set(
        df[col].dropna().unique()
    )

    unexpected_values = (
        actual_values - set(allowed_set)
    )

    passed = len(unexpected_values) == 0

    return {
        "check_name": f"Allowed values - {col}",
        "status": "PASS" if passed else "FAIL",
        "value_found": (
            sorted(actual_values)
            if passed
            else sorted(unexpected_values)
        ),
        "threshold": sorted(allowed_set),
        "severity": "CRITICAL"
    }


# ============================================================
# 4. ROW COUNT CHECK
# ============================================================

def check_row_count(df, expected_min):
    """
    Check whether the dataset contains at least
    the expected minimum number of rows.
    """

    actual_count = len(df)

    passed = actual_count >= expected_min

    return {
        "check_name": "Row count",
        "status": "PASS" if passed else "FAIL",
        "value_found": actual_count,
        "threshold": f">= {expected_min}",
        "severity": "CRITICAL"
    }


# ============================================================
# 5. DUPLICATE CHECK
# ============================================================

def check_no_duplicates(df, key_col):
    """
    Check that the key column contains no duplicates.
    """

    duplicate_count = (
        df[key_col]
        .duplicated()
        .sum()
    )

    passed = duplicate_count == 0

    return {
        "check_name": f"No duplicates - {key_col}",
        "status": "PASS" if passed else "FAIL",
        "value_found": f"{duplicate_count} duplicate rows",
        "threshold": "0 duplicates",
        "severity": "CRITICAL"
    }


# ============================================================
# 6. CHURN DISTRIBUTION CHECK
# ============================================================

def check_churn_distribution(df):
    """
    Check that both churn classes are present.

    After CustomerCleaner, churn is encoded as:
        0 = No
        1 = Yes

    This is a WARNING-level sanity check.
    """

    if "churn" not in df.columns:
        return {
            "check_name": "Churn distribution",
            "status": "FAIL",
            "value_found": "churn column not found",
            "threshold": "Both 0 and 1 classes present",
            "severity": "WARNING"
        }

    distribution = (
        df["churn"]
        .value_counts()
        .to_dict()
    )

    unique_values = set(
        df["churn"]
        .dropna()
        .unique()
    )

    expected_classes = {0, 1}

    passed = expected_classes.issubset(
        unique_values
    )

    return {
        "check_name": "Churn distribution",
        "status": "PASS" if passed else "FAIL",
        "value_found": distribution,
        "threshold": "Both 0 and 1 classes present",
        "severity": "WARNING"
    }

# ============================================================
# RUN ALL QUALITY CHECKS
# ============================================================

def run_quality_checks(df):
    """
    Run all six DE7 quality checks.
    """

    logger.info("Starting data quality checks...")

    results = []

    # --------------------------------------------------------
    # CHECK 1: monthly_charges null rate
    # --------------------------------------------------------

    results.append(
        check_null_rate(
            df,
            "monthly_charges",
            0
        )
    )

    # --------------------------------------------------------
    # CHECK 2: tenure null rate
    # --------------------------------------------------------

    results.append(
        check_null_rate(
            df,
            "tenure",
            0
        )
    )

    # --------------------------------------------------------
    # CHECK 3: tenure range
    # --------------------------------------------------------

    results.append(
        check_value_range(
            df,
            "tenure",
            0,
            100
        )
    )

    # --------------------------------------------------------
    # CHECK 4: monthly_charges > 0
    # --------------------------------------------------------

    results.append(
        check_value_range(
            df,
            "monthly_charges",
            0.000001,
            None
        )
    )

    # --------------------------------------------------------
    # CHECK 5: contract allowed values
    # --------------------------------------------------------

    results.append(
        check_allowed_values(
            df,
            "contract",
            {
                "Month-to-month",
                "One year",
                "Two year"
            }
        )
    )

    # --------------------------------------------------------
    # CHECK 6: row count
    # --------------------------------------------------------

    results.append(
        check_row_count(
            df,
            7000
        )
    )

    # --------------------------------------------------------
    # CHECK 7: duplicate customer IDs
    # --------------------------------------------------------

    results.append(
        check_no_duplicates(
            df,
            "customer_id"
        )
    )

    # --------------------------------------------------------
    # CHECK 8: churn distribution
    # --------------------------------------------------------

    results.append(
        check_churn_distribution(df)
    )

    return results


# ============================================================
# DISPLAY QUALITY RESULTS
# ============================================================

def display_results(results):

    print("\n" + "=" * 70)
    print("DE7 DATA QUALITY REPORT")
    print("=" * 70)

    for result in results:

        print(
            f"{result['status']:4} | "
            f"{result['severity']:8} | "
            f"{result['check_name']}"
        )

        print(
            f"      Value     : "
            f"{result['value_found']}"
        )

        print(
            f"      Threshold : "
            f"{result['threshold']}"
        )

    print("=" * 70)


# ============================================================
# SAVE QUALITY REPORT
# ============================================================

def save_quality_report(results):

    os.makedirs(
        os.path.dirname(REPORT_PATH),
        exist_ok=True
    )

    report = {
        "pipeline": "DE7 Data Quality Checks",
        "file": CSV_PATH,
        "checks": results
    }

    with open(
        REPORT_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4,
            default=str
        )

    logger.info(
        f"Quality report saved to {REPORT_PATH}"
    )


# ============================================================
# CRITICAL FAILURE GATE
# ============================================================

def enforce_quality_gate(results):

    critical_failures = [
        result
        for result in results
        if (
            result["status"] == "FAIL"
            and result["severity"] == "CRITICAL"
        )
    ]

    warning_failures = [
        result
        for result in results
        if (
            result["status"] == "FAIL"
            and result["severity"] == "WARNING"
        )
    ]

    # --------------------------------------------------------
    # WARNING FAILURES
    # --------------------------------------------------------

    for result in warning_failures:

        logger.warning(
            f"WARNING: {result['check_name']} failed. "
            f"Value={result['value_found']}, "
            f"Threshold={result['threshold']}"
        )

    # --------------------------------------------------------
    # CRITICAL FAILURES
    # --------------------------------------------------------

    if critical_failures:

        logger.error(
            "CRITICAL DATA QUALITY CHECK FAILED."
        )

        for result in critical_failures:

            logger.error(
                f"{result['check_name']} | "
                f"Value={result['value_found']} | "
                f"Threshold={result['threshold']}"
            )

        raise RuntimeError(
            "DE7 quality gate failed. "
            "Pipeline stopped because a CRITICAL "
            "data quality check failed."
        )

    logger.info(
        "All CRITICAL data quality checks passed."
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n" + "=" * 70)
    print("DE7 DATA QUALITY PIPELINE")
    print("=" * 70)

    try:

        # ----------------------------------------------------
        # 1. Read CSV
        # ----------------------------------------------------

        logger.info(
            "Reading customer data..."
        )

        df = pd.read_csv(
            CSV_PATH
        )

        logger.info(
            f"Rows read from CSV: {len(df)}"
        )

        # ----------------------------------------------------
        # 2. Reuse existing cleaning pipeline
        # ----------------------------------------------------

        logger.info(
            "Starting data cleaning pipeline..."
        )

        cleaner = CustomerCleaner(df)

        clean_df = cleaner.clean()

        logger.info(
            f"Rows after cleaning: {len(clean_df)}"
        )

        # ----------------------------------------------------
        # 3. Run quality checks
        # ----------------------------------------------------

        results = run_quality_checks(
            clean_df
        )

        # ----------------------------------------------------
        # 4. Display results
        # ----------------------------------------------------

        display_results(
            results
        )

        # ----------------------------------------------------
        # 5. Save JSON report
        # ----------------------------------------------------

        save_quality_report(
            results
        )

        # ----------------------------------------------------
        # 6. Enforce quality gate
        # ----------------------------------------------------

        enforce_quality_gate(
            results
        )

        print("\n" + "=" * 70)
        print(
            "DE7 DATA QUALITY CHECKS PASSED"
        )
        print("=" * 70)

    except Exception as e:

        logger.error(
            f"DE7 FAILED: {e}"
        )

        raise


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()