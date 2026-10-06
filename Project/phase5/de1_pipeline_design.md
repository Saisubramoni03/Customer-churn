# DE1 — Data Engineering Pipeline Design

## 1. Objective

Design the batch customer data pipeline from the raw CRM extract to ML-ready data and API/dashboard consumption.

The pipeline is designed for daily customer extracts and follows:

**CRM Extract → Raw File → Staging → Cleaning → Feature Engineering → ML Scoring → Dashboard/API**

---

## 2. Pipeline Architecture

```text
CRM Extract
     |
     v
Raw CSV
     |
     v
Staging Table (MySQL)
     |
     v
Cleaned Table
(CustomerCleaner)
     |
     v
Feature Table
     |
     v
ML Scoring
     |
     v
Dashboard / API
```

### Layer Mapping

| Layer           | Format           | Tool            | Next Consumer   |
| ---------------- | ---------------- | --------------- | --------------- |
| CRM Extract      | Customer records | CRM              | Raw File         |
| Raw File          | CSV              | Python / Pandas  | Staging          |
| Staging           | MySQL table       | MySQL            | Cleaning         |
| Cleaned            | MySQL / CSV        | CustomerCleaner  | Features         |
| Features           | MySQL / CSV        | Python           | ML               |
| ML Scoring          | Predictions        | Python / ML      | API / Dashboard  |
| API / Dashboard     | JSON / UI          | FastAPI / React  | End User         |

---

## 3. Quality Gates

### Gate 1 — Schema Validation

Performed before loading data into the staging table.

Checks:

- Required columns exist.
- Expected file structure is present.
- Input format is valid.

If validation fails, the input is rejected and the pipeline stops.

### Gate 2 — Data Quality Check

Performed after cleaning and before feature engineering.

Checks:

- `monthly_charges` contains no null values.
- `churn` contains only `0` and `1`.
- Required data is valid for downstream processing.

If the check fails, the pipeline stops and logs the error.

---

## 4. Incremental Processing Strategy

The pipeline processes customer data daily.

The same customer may appear in multiple extracts, so the customer ID is used to identify existing records.

```text
Customer arrives
      |
      v
Already exists?
   /       \
 Yes       No
 |          |
UPDATE    INSERT
```

Existing customers are updated with the latest information, while new customers are inserted.

This prevents duplicate customer records and supports idempotent processing.

---

## 5. Reuse of Existing Project Components

The Data Engineering pipeline reuses logic already developed in Phase 1.

```text
CP2 → CustomerCleaner → DE3 Cleaning
CP4 → Feature Engineering → DE4 Features
CP5 → End-to-End Pipeline → DE Pipeline
```

This avoids duplicating cleaning and feature engineering logic.

---

## 6. Lab Mapping

| Pipeline Component     | Lab      |
| ----------------------- | -------- |
| Ingestion                | DE2      |
| Cleaning                 | DE3      |
| Feature Engineering      | DE4      |
| PySpark Analytics        | DE5      |
| ML Scoring               | ML Phase |
| Dashboard / API          | Phase 4  |
| Pipeline Orchestration   | DE7      |

---

## Summary

The DE1 design establishes a batch customer intelligence pipeline:

**CRM Extract → Raw CSV → Staging → Cleaning → Features → ML Scoring → API/Dashboard**

The architecture includes schema validation, data quality checks, incremental upsert processing, and reuse of the Phase 1 components.