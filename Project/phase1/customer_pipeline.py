import os
import logging
from datetime import datetime

import pandas as pd

from customer_cleaner import CustomerCleaner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

def load_data(filepath):
    try:
        logger.info("Loading dataset...")

        df = pd.read_csv(filepath)

        logger.info(f"Rows loaded: {len(df)}")

        return df

    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise

def build_features(df):
    try:
        logger.info("Building engineered features...")

        feature_df = df.copy()

        # -------------------------------------------------
        # Feature 1 - Tenure Bucket
        # -------------------------------------------------
        feature_df["tenure_bucket"] = pd.cut(
            feature_df["tenure"],
            bins=[0, 12, 24, 48, 72],
            labels=["0-12", "13-24", "25-48", "49-72"],
            include_lowest=True
        )

        # -------------------------------------------------
        # Feature 2 - High Charge Flag
        # -------------------------------------------------
        median_charge = feature_df["monthly_charges"].median()

        feature_df["high_charge_flag"] = (
            feature_df["monthly_charges"] > median_charge
        ).astype(int)

        # -------------------------------------------------
        # Feature 3 - Service Count
        # -------------------------------------------------
        service_columns = [
            "online_security",
            "online_backup",
            "device_protection",
            "tech_support",
            "streaming_tv",
            "streaming_movies"
        ]

        feature_df["service_count"] = feature_df[service_columns].sum(axis=1)

        # -------------------------------------------------
        # Feature 4 - Long Term Customer
        # -------------------------------------------------
        feature_df["is_long_term_customer"] = (
            feature_df["tenure"] >= 24
        ).astype(int)

        # -------------------------------------------------
        # Feature 5 - Streaming Bundle
        # -------------------------------------------------
        feature_df["has_streaming_bundle"] = (
            (feature_df["streaming_tv"] == 1)
            &
            (feature_df["streaming_movies"] == 1)
        ).astype(int)

        # -------------------------------------------------
        # Feature 6 - Auto Pay Flag
        # -------------------------------------------------
        feature_df["auto_pay_flag"] = (
            feature_df["payment_method"]
            .str.contains("automatic", case=False)
        ).astype(int)

        logger.info("Feature engineering completed.")

        return feature_df

    except Exception as e:
        logger.error(f"Feature engineering failed: {e}")
        raise

def save_outputs(clean_df, feature_df, output_dir):
    try:
        logger.info("Saving output files...")

        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d")

        cleaned_file = os.path.join(
            output_dir,
            f"cleaned_customer_{timestamp}.csv"
        )

        feature_file = os.path.join(
            output_dir,
            f"customer_features_{timestamp}.csv"
        )

        clean_df.to_csv(cleaned_file, index=False)
        feature_df.to_csv(feature_file, index=False)

        logger.info(f"Cleaned dataset saved: {cleaned_file}")
        logger.info(f"Feature dataset saved: {feature_file}")

    except Exception as e:
        logger.error(f"Saving failed: {e}")
        raise

def main():

    try:
        logger.info("=" * 60)
        logger.info("CUSTOMER DATA PIPELINE STARTED")
        logger.info("=" * 60)

        current_dir = os.path.dirname(__file__)

        csv_path = "customer_churn.csv"

        output_dir = os.path.join(
            current_dir,
            "output"
        )

        # Load
        raw_df = load_data(csv_path)

        # Clean
        clean_df = CustomerCleaner(raw_df).clean()

        # Features
        feature_df = build_features(clean_df)

        # -------------------------
        # Data Quality Checks
        # -------------------------

        assert clean_df["monthly_charges"].isnull().sum() == 0, \
            "monthly_charges contains null values."

        assert set(clean_df["churn"].unique()) <= {0, 1}, \
            "churn column contains invalid values."

        logger.info("Data quality checks passed.")

        # Save
        save_outputs(
            clean_df,
            feature_df,
            output_dir
        )

        logger.info("=" * 60)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()  