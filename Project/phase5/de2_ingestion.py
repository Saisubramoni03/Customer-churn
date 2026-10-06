import csv
import shutil
from pathlib import Path
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os


# ============================================================
# PATH CONFIGURATION
# ============================================================

# Project/
# ├── .env
# └── phase5/
#     └── de2_ingestion.py

PHASE5_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PHASE5_DIR.parent

DATA_DIR = PHASE5_DIR / "data"

LANDING_DIR = DATA_DIR / "landing"
RAW_DIR = DATA_DIR / "raw"
REJECTED_DIR = DATA_DIR / "rejected"
LOG_DIR = DATA_DIR / "logs"


# Create required folders if they do not exist
LANDING_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)
REJECTED_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

ENV_FILE = PROJECT_DIR / ".env"

load_dotenv(ENV_FILE)


# ============================================================
# DATABASE CONNECTION
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Alternative configuration if DATABASE_URL is not present
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "customer_retention")

    DATABASE_URL = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )


engine = create_engine(DATABASE_URL)


# ============================================================
# EXPECTED CSV SCHEMA
# ============================================================

EXPECTED_COLS = [
    "customerID",
    "gender",
    "SeniorCitizen",
    "Partner",
    "Dependents",
    "tenure",
    "PhoneService",
    "MultipleLines",
    "InternetService",
    "OnlineSecurity",
    "OnlineBackup",
    "DeviceProtection",
    "TechSupport",
    "StreamingTV",
    "StreamingMovies",
    "Contract",
    "PaperlessBilling",
    "PaymentMethod",
    "MonthlyCharges",
    "TotalCharges",
    "Churn"
]


# ============================================================
# 1. DETECT FILES
# ============================================================

def detect_files():
    """
    Scan the landing folder and return all CSV files.
    """

    files = list(LANDING_DIR.glob("*.csv"))

    print("Detected files:")

    for file in files:
        print(file)

    return files


# ============================================================
# 2. VALIDATE SCHEMA
# ============================================================

def validate_schema(filepath):
    """
    Read only the header row and compare it with EXPECTED_COLS.

    Returns:
        (True/False, actual_columns)
    """

    with open(filepath, "r", encoding="utf-8-sig", newline="") as f:

        reader = csv.reader(f)

        header = next(reader)

    is_valid = header == EXPECTED_COLS

    return is_valid, header


# ============================================================
# 3. CREATE INGESTION LOG TABLE
# ============================================================

def create_ingestion_log_table():
    """
    Create ingestion_log table if it does not already exist.
    """

    query = text("""
        CREATE TABLE IF NOT EXISTS ingestion_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            status VARCHAR(50) NOT NULL,
            row_count INT DEFAULT 0,
            reason TEXT,
            loaded_at DATETIME NOT NULL
        )
    """)

    with engine.begin() as connection:
        connection.execute(query)


# ============================================================
# 4. LOAD TO STAGING
# ============================================================

def load_to_staging(filepath):
    """
    Load a valid CSV file into stg_customer_raw.

    The staging table is replaced on every successful load.
    """

    df = pd.read_csv(filepath)

    df.to_sql(
        "stg_customer_raw",
        engine,
        if_exists="replace",
        index=False
    )

    return len(df)


# ============================================================
# 5. LOG INGESTION
# ============================================================

def log_ingestion(filename, status, rows, reason):
    """
    Insert an ingestion result into ingestion_log.
    """

    query = text("""
        INSERT INTO ingestion_log
        (
            filename,
            status,
            row_count,
            reason,
            load_time
        )
        VALUES
        (
            :filename,
            :status,
            :row_count,
            :reason,
            :load_time
        )
    """)

    with engine.begin() as connection:

        connection.execute(
            query,
            {
                "filename": filename,
                "status": status,
                "row_count": rows,
                "reason": reason,
                "load_time": datetime.now()
            }
        )


# ============================================================
# 6. MOVE REJECTED FILE
# ============================================================

def move_to_rejected(filepath):
    """
    Move an invalid file to the rejected folder.
    """

    destination = REJECTED_DIR / filepath.name

    shutil.move(str(filepath), str(destination))

    return destination


# ============================================================
# 7. PROCESS LANDING
# ============================================================

def process_landing():

    print("=" * 60)
    print("DE2 INGESTION PIPELINE")
    print("=" * 60)

    create_ingestion_log_table()

    files = detect_files()

    if not files:
        print("No CSV files found in landing folder.")
        return

    for filepath in files:

        print()
        print("-" * 60)
        print(f"Processing: {filepath}")
        print("-" * 60)

        try:

            # ------------------------------------------------
            # Schema validation
            # ------------------------------------------------

            schema_valid, columns = validate_schema(filepath)

            print(f"Schema valid: {schema_valid}")
            print(f"Columns found: {len(columns)}")

            if not schema_valid:

                missing_columns = [
                    column
                    for column in EXPECTED_COLS
                    if column not in columns
                ]

                extra_columns = [
                    column
                    for column in columns
                    if column not in EXPECTED_COLS
                ]

                reason_parts = []

                if missing_columns:
                    reason_parts.append(
                        f"Missing columns: {missing_columns}"
                    )

                if extra_columns:
                    reason_parts.append(
                        f"Unexpected columns: {extra_columns}"
                    )

                if not missing_columns and not extra_columns:
                    reason_parts.append(
                        "Column names or column order does not match expected schema."
                    )

                reason = " ".join(reason_parts)

                print("STATUS: REJECTED")
                print(f"Reason: {reason}")

                log_ingestion(
                    filename=filepath.name,
                    status="REJECTED",
                    rows=0,
                    reason=reason
                )

                move_to_rejected(filepath)

                continue

            # ------------------------------------------------
            # Load valid file
            # ------------------------------------------------

            row_count = load_to_staging(filepath)

            print("STATUS: LOADED")
            print(f"Rows loaded: {row_count}")

            log_ingestion(
                filename=filepath.name,
                status="LOADED",
                rows=row_count,
                reason="Schema validation successful"
            )

            # ------------------------------------------------
            # Move successfully processed file to raw
            # ------------------------------------------------

            raw_destination = RAW_DIR / filepath.name

            shutil.move(
                str(filepath),
                str(raw_destination)
            )

            print(f"Moved to raw: {raw_destination}")

        except Exception as e:

            print("STATUS: ERROR")
            print(f"Error: {e}")

            log_ingestion(
                filename=filepath.name,
                status="ERROR",
                rows=0,
                reason=str(e)
            )

            raise


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print()
    print("Starting DE2 ingestion...")

    try:

        process_landing()

        print()
        print("=" * 60)
        print("DE2 INGESTION COMPLETED")
        print("=" * 60)

    except Exception as e:

        print()
        print("=" * 60)
        print("DE2 INGESTION FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        raise