# Customer Retention / Churn Prediction Project

## Purpose

This project is an end-to-end customer-retention system built around the Telco Customer Churn data set. It profiles and cleans CRM extracts, engineers churn features, loads curated data into MySQL, trains and serves churn models, and exposes the results through a FastAPI service and a React/Vite dashboard. The implemented path is:

```text
CRM/CSV extract
  -> Phase 5 landing, schema gate, and staging
  -> Phase 1-compatible cleaning
  -> curated MySQL tables and ML feature table
  -> Phase 6 model training or scoring
  -> FastAPI endpoints
  -> Phase 4 React dashboard
```

The repository contains both instructional phase scripts and the integrated root application. The root `main.py` is the API used by the current dashboard.

## Architecture

### Runtime components

* **Data source:** CSV records with customer demographics, tenure, services, contract, billing, and `Churn`.
* **Storage:** MySQL database `customer_retention`. SQLAlchemy is used by the API and most pipeline stages; pandas `to_sql` is used for bulk writes.
* **Backend:** FastAPI application at port 8000. Root `main.py` registers routers for customers, analytics, features, high-risk customers, and prediction.
* **ML:** Phase 6 loads a serialized Decision Tree (`tree_churn.pkl`) for online prediction. Logistic Regression and Decision Tree artifacts are produced by model training.
* **Frontend:** Phase 4 React 19/Vite application at port 3000. Axios calls the API and adds the `X-API-Key` header.
* **Batch/analytics artifacts:** Phase 5 writes cleaned/feature data, quality JSON, and a Spark contract-summary Parquet file; Phase 6 can write a `customer_risk_table` and high-risk CSV output.

The database integration uses separate curated tables (`customers`, `contracts`, `billing`, `services`, and `customer_status`) rather than one denormalized API table. Customer IDs connect the tables. The current setup documentation reports 7,043 records, including 1,869 churned and 5,174 retained customers; the `services` table is documented as optional/empty in that setup snapshot.

## Phases

### Phase 1 — profiling, cleaning, insights, and features

`phase1/cp1_data_profiling.py` profiles shape, types, nulls, categorical distributions, churn balance, `TotalCharges`, and numeric statistics. `customer_cleaner.py` is the reusable cleaning component:

1. Convert mixed-case column names to lowercase snake case.
2. Convert blank/non-numeric `total_charges` values to numeric/NA.
3. Encode Yes/No and “No internet service” binary columns as 1/0.
4. Fill missing `total_charges` with `monthly_charges` (appropriate for zero-tenure rows).

`customer_pipeline.py` runs load → clean → feature engineering → assertions → timestamped CSV output. Its quality gates require non-null `monthly_charges` and churn values contained in `{0, 1}`. `cp3_business_insights.py` computes churn by contract, internet service, payment method, tenure bucket, and segments, and compares average monthly charges by churn status. `cp4_feature_engineering.py` creates:

* `tenure_bucket` (`0-12`, `13-24`, `25-48`, `49-72`)
* `high_charge_flag` (above the data median)
* `service_count`
* `is_long_term_customer` (tenure ≥ 24)
* `has_streaming_bundle` (TV and movies)
* `auto_pay_flag` (payment method containing “automatic”)

The feature script also prints correlations with churn and writes `customer_features.csv`.

### Phase 4 — dashboard

The React app has four client-side tabs:

* **Summary:** total customers, churned customers, overall rate, and contract-level bars.
* **Customer Search:** concurrently fetches `/customers/{id}/profile` and `/features/{id}` and merges the responses.
* **High Risk:** fetches churned customers, displays a selectable first 50, supports “load more,” and sorts by tenure.
* **Prediction:** posts tenure, monthly charges, contract, service count, and optional customer ID to `/predict-churn`; it presents score, label, and confidence.

`src/api.js` defaults to `http://localhost:8000` and `mysecret123`, while allowing `VITE_API_URL` and `VITE_API_KEY` overrides. `App.jsx` provides tab state and page composition; CSS files provide the dashboard layout and visual states. Vite scripts support development, production build, preview, and ESLint.

### Phase 5 — data engineering

The design document defines **CRM Extract → Raw CSV → Staging → Cleaning → Features → ML Scoring → API/Dashboard**, with schema validation before staging and data-quality validation before features.

* **DE2 ingestion:** creates landing/raw/rejected/log directories, detects landing CSVs, requires an exact 21-column header, loads valid files to `stg_customer_raw`, logs outcomes, moves valid files to `data/raw`, and rejects invalid files. It also creates `ingestion_log`.
* **DE3 cleaning:** reads staging, reuses Phase 1 `CustomerCleaner`, checks row-count preservation, writes `cleaned_customers`, validates IDs, charges, and churn values, and repopulates the curated tables. It deliberately clears dependent tables before customers.
* **DE4 features:** reads `cleaned_customers`, derives the six feature families above, writes `customer_ml_features`, and validates row counts, required columns, and null absence.
* **DE5 Spark:** reads the raw CSV with an explicit schema, converts `TotalCharges`, encodes churn, aggregates by contract and internet service, validates the three contract groups, and writes/round-trips `contract_summary.parquet`. It includes a PyArrow/pandas fallback for Windows Hadoop/winutils limitations.
* **DE6 incremental processing:** is intended to upsert daily records by customer ID (update existing, insert new), preserving idempotence. Its implementation is present in `de6_incremental.py` and should be treated as a batch utility rather than a continuously running service.
* **DE7 quality:** reuses `CustomerCleaner`, checks null rates, ranges, allowed contract values, minimum row count (7,000), duplicate IDs, and both churn classes, emits `data/logs/quality_report.json`, and stops on critical failures.

`phase5/db.py` supplies the phase pipeline’s SQLAlchemy engine from `DATABASE_URL`.

### Phase 6 — machine learning

`ml1_problem_setup.py` loads `cleaned_customers`, builds the ML feature table, separates `customer_id` and `churn`, and one-hot encodes contract and internet service. The final online feature contract has 14 columns: tenure, monthly and total charges, service count, four derived flags, three contract indicators, and three internet-service indicators.

`ml2_model_training.py` performs a stratified 80/20 split (`random_state=42`), trains Logistic Regression (`max_iter=1000`) and a depth-5 Decision Tree, evaluates accuracy, precision, recall, F1 for churn, confusion matrices, and five-fold F1 cross-validation, selects by churn F1, and saves both models with joblib. `ml3_interpretation.py` supplies the interpretation/reporting stage and the repository includes `outputs/top_feature_importance.png`.

`predict.py` loads the Decision Tree once at import time. It reconstructs the exact 14-column input from four API fields, using:

* `total_charges = tenure * monthly_charges`
* charge threshold 70
* long-term threshold 24 months
* streaming/auto-pay heuristics based on service count, tenure, and charge
* contract one-hot encoding
* internet-service inference from monthly charges (high = Fiber optic, low = No, otherwise DSL)

It returns a percentage `risk_score`, “Likely to churn”/“Unlikely to churn,” and a confidence percentage. `batch_score.py` applies the same predictor to all cleaned customers, writes `customer_risk_table`, prints a summary/top ten, and the checked-in Phase 6 outputs include `top_20_high_risk_customers.csv` and the feature-importance image.

## Backend API

### Application and cross-cutting behavior

`main.py` creates a titled/versioned FastAPI app, enables CORS for localhost ports 3000, 3001, and 5173, and registers all routers. Database sessions are yielded by `database/dependencies.py` and closed in `finally`. `database/security.py` reads `API_KEY` and requires an exact `X-API-Key` match; currently only prediction is protected by this dependency. `database/logger.py` provides application logging.

### Routes

| Method | Path | Behavior |
|---|---|---|
| GET | `/` | Health message. |
| GET | `/customers` | Paginated customer list (`skip`, `limit`, default 10, max 100). |
| GET | `/customers/search` | Filters customers by optional `gender` and `contract_type`. |
| GET | `/customers/{customer_id}` | Basic profile or 404. |
| GET | `/customers/{customer_id}/profile` | Joins demographics, contract, billing, optional service, and churn status. |
| GET | `/customers/high-risk` | Returns `churn = 1` customers, ordered by ascending tenure; services are a left join. |
| GET | `/features/{customer_id}` | Returns billing, contract, payment, tenure, and optional internet service. |
| GET | `/churn/summary` | Full summary including contract and internet-service breakdowns. |
| GET | `/analytics/churn-summary` | Smaller total/churned/rate summary (legacy/parallel analytics route). |
| POST | `/predict-churn` | Validates request, checks API key, and delegates to Phase 6 prediction. |

SQLAlchemy failures generally return a 500 JSON body with `detail: "Database unavailable"`. Missing customers return 404. The prediction router returns a safe fallback response if the model cannot be imported or prediction raises an exception.

## Database models

`database/models.py` defines SQLAlchemy mappings:

* `Customer` → `customers`: `customer_id` primary key, gender, senior-citizen, partner, dependents.
* `Contract` → `contracts`: auto-increment ID, customer ID, contract type.
* `Billing` → `billing`: auto-increment ID, customer ID, tenure, paperless billing, payment method, monthly and total charges (`DECIMAL`).
* `Service` → `services`: phone, lines, internet, security, backup, protection, support, TV, and movies.
* `CustomerStatus` → `customer_status`: auto-increment ID, customer ID, integer churn label.

The model classes do not declare SQLAlchemy relationships or foreign keys; joins are explicit in router queries and pipeline SQL. `init_db.py` creates these tables with `Base.metadata.create_all`. `check_db_schema.py` inspects the separately generated `customer_ml_features` table.

## Configuration and dependencies

The root `.env` supplies MySQL host/port/user/password/name, `API_KEY`, and `DATABASE_URL`; the checked-in values are development credentials and must be replaced in a real deployment. `phase4/.env` is intended for Vite API URL/key overrides. `requirements.txt` pins Python dependencies including FastAPI, Uvicorn, Pydantic, SQLAlchemy, PyMySQL, pandas, NumPy, scikit-learn/joblib-related ML tooling, python-dotenv, PySpark support, and notebook/runtime packages. `phase4/package.json` pins React, React DOM, Axios, Vite, the React plugin, ESLint, and React ESLint plugins.

Typical commands:

```text
python init_db.py
uvicorn main:app --reload --port 8000
cd phase4
npm install
npm run dev
```

The setup documentation describes the frontend on `:3000`, API on `:8000`, and MySQL on `localhost:3306`; Swagger is available at `/docs`.

## Execution flows

### Online dashboard flow

1. Browser loads the Vite bundle.
2. Axios adds JSON content type and `X-API-Key`.
3. A dashboard page calls the relevant FastAPI route.
4. FastAPI validates Pydantic input/output and either queries MySQL or invokes Phase 6.
5. SQLAlchemy closes the session after database work.
6. JSON is rendered into cards, tables, or prediction results.

### Data-to-model flow

1. DE2 validates and stages an extract.
2. DE3 cleans it and populates curated tables.
3. DE4 derives and validates ML features.
4. ML1/ML2 prepare, train, evaluate, and serialize models.
5. Online `predict.py` or `batch_score.py` recreates the same feature order.
6. API/dashboard or the risk table consumes predictions.

## Tests and validation assets

The repository does not use a conventional pytest/unittest suite. The executable checks are scripts:

* `test_connection.py` executes `SELECT DATABASE()` through the configured engine.
* `test_orm.py` opens a SQLAlchemy session and prints sample `Customer` rows.
* `test_high_risk.py` exercises the live prediction endpoint with high/low examples and an API key.
* `test_ml_prediction.py` runs a broader six-case live prediction smoke suite.
* `check_db_schema.py` prints the ML feature-table columns and a sample.
* Phase 1, DE3, DE4, DE5, and DE7 contain assertions and validation gates described above.
* `test_prediction.json` is a sample prediction payload.

## Limitations and operational cautions

* The API depends on a reachable MySQL instance and correctly populated tables; startup does not verify connectivity.
* Environment files contain weak, development-style credentials and a placeholder-looking `DATABASE_URL` value in the checked-in snapshot. Secrets should not be committed.
* API-key protection is applied to prediction but not consistently to read endpoints; CORS is limited to configured localhost origins.
* The ORM models lack declared relationships/foreign keys, and most joins rely on unconstrained customer-ID matches.
* `services` may be empty; the high-risk route intentionally uses `LEFT JOIN`, but other data completeness assumptions remain.
* `predict.py` infers several features from only four user inputs instead of retrieving the customer’s complete service/billing record. Its thresholds and heuristics can differ from training-time feature engineering.
* Model artifacts are binary, have no recorded training metrics/version metadata, and require compatible Python/scikit-learn/joblib environments.
* Several scripts use relative paths and are intended to be run from their phase directory. DE2’s ingestion-log SQL uses `load_time` while its table definition declares `loaded_at`, which can fail when logging.
* DE4’s feature-table shape must match the ML2 contract; alternate phase scripts may create different subsets, so pipeline order matters.
* Spark’s native Windows Parquet path may require `winutils.exe`; the script’s fallback depends on PyArrow or an installed pandas Parquet engine.
* Batch scoring replaces `customer_risk_table` rather than retaining historical scores.
* The frontend has no authentication UI, routing library, pagination API integration, or automated component tests; “load more” only reveals more rows already returned by the high-risk endpoint.
* The live test scripts assume the API is already running and contain hard-coded local URLs/API keys.

## Source-file inventory

Paths below are project-owned source, configuration, documentation, test, and checked-in data/artifact files. Generated/dependency directories (`venv`, `.venv`, `node_modules`, `dist`, and `__pycache__`) are intentionally excluded.

### Root

* `main.py` — integrated FastAPI app.
* `requirements.txt` — Python dependency pins.
* `.env` — local database/API configuration.
* `init_db.py`, `check_db_schema.py` — database setup and inspection.
* `customer_churn.csv` — root data extract.
* `test_connection.py`, `test_orm.py`, `test_high_risk.py`, `test_ml_prediction.py` — executable smoke checks.
* `test_prediction.json` — sample request data.
* `SETUP_COMPLETE.md` — integration/runbook snapshot.
* `phase6.zip` — checked-in archive artifact.

### `database/`

* `database.py` — dotenv-driven MySQL SQLAlchemy engine/session/base.
* `dependencies.py` — FastAPI session dependency.
* `models.py` — curated-table ORM models.
* `security.py` — API-key dependency.
* `logger.py` — logger setup.

### `routers/`

* `customers.py` — customer list, search, profile, and ID routes.
* `high_risk.py` — churned-customer route.
* `features.py` — feature/profile route.
* `churn.py` — detailed churn summary route.
* `churn_summary.py` — compact analytics summary route.
* `prediction.py` — API-key-protected Phase 6 adapter.

### `schemas/`

* `customer.py` — customer/list/profile response models.
* `features.py` — feature response model.
* `high_risk.py` — high-risk response model.
* `prediction.py` — prediction request/response models.
* `churn.py`, `churn_summary.py` — summary response models.
* `error.py` — error schema module.

### `phase1/`

* `cp1_data_profiling.py` — profiling.
* `cp2_test_cleaner.py` — cleaner checks.
* `cp3_business_insights.py` — segment analysis.
* `cp4_feature_engineering.py` — feature generation/correlation.
* `customer_cleaner.py` — reusable cleaning class.
* `customer_pipeline.py` — end-to-end local pipeline.
* `customer_churn.csv`, `customer_features.csv` — phase inputs/outputs.
* `output/cleaned_customer_*.csv`, `output/customer_features_*.csv` — timestamped outputs.

### `phase4/`

* `package.json`, `package-lock.json` — frontend dependencies/scripts.
* `vite.config.js`, `eslint.config.js`, `index.html`, `.env`, `.gitignore` — frontend configuration.
* `src/main.jsx`, `src/App.jsx`, `src/api.js` — app bootstrap, shell, API client.
* `src/pages/ChurnSummary.jsx`, `CustomerSearch.jsx`, `HighRiskCustomers.jsx`, `ChurnPrediction.jsx` — dashboard pages.
* `src/App.css`, `src/index.css` — styles.
* `public/favicon.svg`, `public/icons.svg`, `src/assets/hero.png`, `src/assets/react.svg`, `src/assets/vite.svg` — public/static assets.
* `README.md` — Vite starter documentation (largely template-oriented).

### `phase5/`

* `de1_pipeline_design.md` — architecture and quality-gate design.
* `db.py` — phase database engine.
* `de2_ingestion.py` — landing/staging ingestion.
* `de3_cleaning.py` — cleaning and curated-table load.
* `de4_features.py` — feature table and validation.
* `de5_spark.py` — Spark analytics and Parquet output.
* `de6_incremental.py` — incremental processing utility.
* `de7_quality.py` — quality report and critical gate.
* `data/raw/*.csv` — raw extracts/backups.
* `data/logs/quality_report.json` — checked-in quality report.
* `data/spark_output/contract_summary/contract_summary.parquet` — Spark result.

### `phase6/`

* `__init__.py` — package marker.
* `ml1_problem_setup.py` — ML feature/problem definition.
* `ml2_model_training.py` — training/evaluation/model persistence.
* `ml3_interpretation.py` — interpretation stage.
* `predict.py` — online feature reconstruction and prediction.
* `batch_score.py` — batch scoring and risk-table output.
* `main.py` — standalone Phase 6 FastAPI variant.
* `models/logistic_churn.pkl`, `models/tree_churn.pkl` — serialized models.
* `outputs/top_20_high_risk_customers.csv`, `outputs/top_feature_importance.png` — checked-in ML outputs.

