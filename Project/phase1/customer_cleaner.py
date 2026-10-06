import logging
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

logger = logging.getLogger(__name__)


class CustomerCleaner:

    def __init__(self, df):
        """
        Initialize the cleaner with a copy of the DataFrame
        so the original data is not modified.
        """
        self.df = df.copy()

    def standardize_column_names(self):
        """
        Convert column names to lowercase snake_case.
        Example:
        MonthlyCharges -> monthly_charges
        customerID -> customer_id
        StreamingTV -> streaming_tv
        """

        logger.info("Standardizing column names...")

        self.df.columns = (
            self.df.columns
            .str.replace(r'(?<=[a-z0-9])(?=[A-Z])', '_', regex=True)
            .str.lower()
            .str.strip()
            .str.replace(" ", "_", regex=False)
        )

        logger.info("Column names converted to snake_case.")

        return self

    def fix_total_charges(self):
        """
        Replace blank strings with NaN and convert
        total_charges to float.
        """

        logger.info("Fixing total_charges column...")

        try:
            blank_count = (
                self.df["total_charges"]
                .astype(str)
                .str.strip()
                .eq("")
                .sum()
            )

            logger.info(f"Blank values found: {blank_count}")

            self.df["total_charges"] = (
                self.df["total_charges"]
                .replace(r'^\s*$', pd.NA, regex=True)
            )

            self.df["total_charges"] = pd.to_numeric(
                self.df["total_charges"],
                errors="coerce"
            )

            nan_count = self.df["total_charges"].isna().sum()

            logger.info(f"NaN after conversion: {nan_count}")

        except Exception as e:
            logger.error(f"Unexpected error while fixing total_charges: {e}")

        return self

    def normalize_binary_columns(self):
        """
        Convert binary Yes/No service columns to 1/0.
        'No internet service' is treated as 0.
        """

        logger.info("Encoding binary columns...")

        binary_columns = [
            "partner",
            "dependents",
            "phone_service",
            "paperless_billing",
            "churn",
            "online_security",
            "online_backup",
            "device_protection",
            "tech_support",
            "streaming_tv",
            "streaming_movies"
        ]

        mapping = {
            "Yes": 1,
            "No": 0,
            "No internet service": 0
        }

        for column in binary_columns:
            self.df[column] = self.df[column].map(mapping)

        logger.info("Binary columns encoded successfully.")

        return self

    def handle_nulls(self):
        """
        Fill missing total_charges with monthly_charges.
        This is appropriate for customers with tenure = 0.
        """

        logger.info("Handling missing values...")

        before = self.df["total_charges"].isna().sum()

        self.df["total_charges"] = self.df["total_charges"].fillna(
            self.df["monthly_charges"]
        )

        after = self.df["total_charges"].isna().sum()

        logger.info(f"Filled {before - after} missing total_charges values.")
        logger.info(f"Remaining null values: {after}")

        return self

    def clean(self):
        """
        Execute all cleaning steps and return
        the cleaned DataFrame.
        """

        logger.info("Starting data cleaning pipeline...")

        cleaned_df = (
            self
            .standardize_column_names()
            .fix_total_charges()
            .normalize_binary_columns()
            .handle_nulls()
            .df
        )

        logger.info("Data cleaning completed successfully.")

        return cleaned_df