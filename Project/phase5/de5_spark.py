import os
import shutil

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    DoubleType
)


# ============================================================
# CONFIGURATION
# ============================================================

CSV_PATH = "data/raw/customer_churn.csv"
OUTPUT_PATH = "data/spark_output/contract_summary"


# ============================================================
# CREATE SPARK SESSION
# ============================================================

spark = (
    SparkSession.builder
    .appName("DE5_Customer_Churn")
    .master("local[2]")
    .config("spark.driver.memory", "4g")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")


print("\n" + "=" * 60)
print("DE5 PYSPARK CUSTOMER PROCESSING")
print("=" * 60)


# ============================================================
# 1. MANUAL SCHEMA
# ============================================================

schema = StructType([

    StructField("customerID", StringType(), True),
    StructField("gender", StringType(), True),
    StructField("SeniorCitizen", IntegerType(), True),
    StructField("Partner", StringType(), True),
    StructField("Dependents", StringType(), True),
    StructField("tenure", IntegerType(), True),
    StructField("PhoneService", StringType(), True),
    StructField("MultipleLines", StringType(), True),
    StructField("InternetService", StringType(), True),
    StructField("OnlineSecurity", StringType(), True),
    StructField("OnlineBackup", StringType(), True),
    StructField("DeviceProtection", StringType(), True),
    StructField("TechSupport", StringType(), True),
    StructField("StreamingTV", StringType(), True),
    StructField("StreamingMovies", StringType(), True),
    StructField("Contract", StringType(), True),
    StructField("PaperlessBilling", StringType(), True),
    StructField("PaymentMethod", StringType(), True),
    StructField("MonthlyCharges", DoubleType(), True),

    # Keep TotalCharges as String initially
    StructField("TotalCharges", StringType(), True),

    StructField("Churn", StringType(), True)
])


# ============================================================
# 2. READ CSV
# ============================================================

print("\nReading customer_churn.csv...")

df = (
    spark.read
    .option("header", True)
    .schema(schema)
    .csv(CSV_PATH)
)

row_count = df.count()

print(f"Rows read: {row_count}")

print("\nSpark schema:")
df.printSchema()


# ============================================================
# 3. FIX TOTALCHARGES
# ============================================================

print("\nCleaning TotalCharges...")

df = df.withColumn(
    "TotalCharges",
    F.regexp_replace(
        F.col("TotalCharges"),
        r"^\s*$",
        None
    ).cast(DoubleType())
)


# ============================================================
# 4. ENCODE CHURN
# ============================================================

print("Encoding Churn...")

df = df.withColumn(
    "churn_encoded",
    F.when(
        F.col("Churn") == "Yes",
        1
    ).otherwise(0)
)


# ============================================================
# 5. GROUP BY CONTRACT
# ============================================================

print("\n" + "=" * 60)
print("CHURN BY CONTRACT")
print("=" * 60)

contract_summary = (
    df.groupBy("Contract")
    .agg(
        F.count("*").alias("customer_count"),
        F.avg("churn_encoded").alias("churn_rate")
    )
    .orderBy("Contract")
)

contract_summary.show(truncate=False)


# ============================================================
# 6. GROUP BY INTERNET SERVICE
# ============================================================

print("\n" + "=" * 60)
print("CHURN BY INTERNET SERVICE")
print("=" * 60)

internet_summary = (
    df.groupBy("InternetService")
    .agg(
        F.avg("MonthlyCharges").alias("avg_monthly_charges"),
        F.avg("churn_encoded").alias("churn_rate")
    )
    .orderBy("InternetService")
)

internet_summary.show(truncate=False)


# ============================================================
# 7. VALIDATE CONTRACT RESULTS
# ============================================================

print("\n" + "=" * 60)
print("CONTRACT SUMMARY VALIDATION")
print("=" * 60)

contract_count = contract_summary.count()

assert contract_count == 3, (
    f"Expected 3 contract groups, found {contract_count}"
)

assert contract_summary.filter(
    F.col("customer_count").isNull()
).count() == 0

assert contract_summary.filter(
    F.col("churn_rate").isNull()
).count() == 0

print("PASS: Contract summary contains 3 groups")
print("PASS: No NULL customer counts")
print("PASS: No NULL churn rates")


# ============================================================
# 8. WRITE PARQUET
#
# IMPORTANT:
# Spark's native Windows Parquet writer requires Hadoop
# filesystem permissions and therefore winutils.exe.
#
# Company laptop restriction:
# We avoid installing winutils.exe.
#
# First try PyArrow if already installed.
# Otherwise try pandas + an existing Parquet engine.
# ============================================================

print("\n" + "=" * 60)
print("WRITING PARQUET")
print("=" * 60)

# Remove previous output if it exists
if os.path.exists(OUTPUT_PATH):
    shutil.rmtree(OUTPUT_PATH)


parquet_written = False


# ------------------------------------------------------------
# Method 1: PyArrow
# ------------------------------------------------------------

try:

    import pyarrow as pa
    import pyarrow.parquet as pq

    print("Using existing PyArrow installation...")

    # Convert Spark result to pandas
    contract_pd = contract_summary.toPandas()

    # Create output directory
    os.makedirs(OUTPUT_PATH, exist_ok=True)

    # Convert pandas -> Arrow
    arrow_table = pa.Table.from_pandas(
        contract_pd,
        preserve_index=False
    )

    # Write one parquet file
    parquet_file = os.path.join(
        OUTPUT_PATH,
        "contract_summary.parquet"
    )

    pq.write_table(
        arrow_table,
        parquet_file
    )

    parquet_written = True

    print(f"Parquet written successfully: {parquet_file}")


except ImportError:

    print("PyArrow is not installed.")


# ------------------------------------------------------------
# Method 2: pandas + existing Parquet engine
# ------------------------------------------------------------

if not parquet_written:

    try:

        import pandas as pd

        print("Trying pandas Parquet writer...")

        contract_pd = contract_summary.toPandas()

        os.makedirs(OUTPUT_PATH, exist_ok=True)

        parquet_file = os.path.join(
            OUTPUT_PATH,
            "contract_summary.parquet"
        )

        contract_pd.to_parquet(
            parquet_file,
            index=False
        )

        parquet_written = True

        print(
            f"Parquet written successfully: {parquet_file}"
        )


    except Exception as e:

        print(
            "Pandas Parquet writer unavailable."
        )

        print(f"Reason: {e}")


# ============================================================
# 9. PARQUET ROUND-TRIP VALIDATION
# ============================================================

print("\n" + "=" * 60)
print("PARQUET ROUND-TRIP VALIDATION")
print("=" * 60)


if parquet_written:

    # --------------------------------------------------------
    # Try reading through Spark
    # --------------------------------------------------------

    try:

        parquet_df = spark.read.parquet(
            OUTPUT_PATH
        )

        print("\nParquet schema:")
        parquet_df.printSchema()

        parquet_count = parquet_df.count()

        print(
            f"Parquet row count: {parquet_count}"
        )

        assert parquet_count == contract_count

        print(
            "\nPASS: Parquet round-trip row count"
        )

        assert set(
            [
                "Contract",
                "customer_count",
                "churn_rate"
            ]
        ).issubset(
            set(parquet_df.columns)
        )

        print(
            "PASS: Parquet schema check"
        )

        print(
            "PASS: Spark successfully read Parquet"
        )


    except Exception as e:

        print(
            "\nSpark Parquet read encountered "
            "the Windows Hadoop limitation."
        )

        print(
            f"Reason: {e}"
        )

        # ----------------------------------------------------
        # Validate with PyArrow/pandas instead
        # ----------------------------------------------------

        try:

            import pyarrow.parquet as pq

            arrow_table = pq.read_table(
                parquet_file
            )

            roundtrip_pd = (
                arrow_table.to_pandas()
            )

            roundtrip_count = len(
                roundtrip_pd
            )

            print(
                f"Parquet row count: {roundtrip_count}"
            )

            assert (
                roundtrip_count == contract_count
            )

            print(
                "PASS: Parquet round-trip row count"
            )

            assert set(
                [
                    "Contract",
                    "customer_count",
                    "churn_rate"
                ]
            ).issubset(
                set(roundtrip_pd.columns)
            )

            print(
                "PASS: Parquet schema check"
            )

            print(
                "PASS: Parquet successfully "
                "validated using PyArrow"
            )


        except Exception as e2:

            print(
                "ERROR: Could not validate "
                "Parquet round-trip."
            )

            print(
                f"Reason: {e2}"
            )

            parquet_written = False


else:

    print(
        "WARNING: Parquet could not be written "
        "without installing an additional package."
    )

    print(
        "Spark processing and aggregations "
        "completed successfully."
    )


# ============================================================
# FINAL STATUS
# ============================================================

print("\n" + "=" * 60)

if parquet_written:

    print(
        "DE5 PYSPARK PIPELINE COMPLETED SUCCESSFULLY"
    )

else:

    print(
        "DE5 PYSPARK PROCESSING COMPLETED"
    )

    print(
        "Parquet step requires a Parquet writer "
        "not currently available."
    )

print("=" * 60)


# ============================================================
# STOP SPARK
# ============================================================

spark.stop()