# Churn Prediction System - Setup Complete ✓

## System Overview
Successfully integrated Phase4 (React Frontend), Phase5 (Data Pipeline), and Phase6 (ML Backend) for customer churn prediction.

---

## Architecture

```
Phase4 (React UI)  ←→  FastAPI Backend (Root main.py)  ←→  MySQL Database
     :3000                    :8000                        (localhost:3306)
                                 ↑
                              Phase5 Data Pipeline
                           (Data Ingestion & Processing)
```

---

## Running Services

### 1. **Backend API (FastAPI)**
- **URL**: `http://localhost:8000`
- **Status**: ✓ Running on port 8000
- **Command**: `uvicorn main:app --reload --port 8000`
- **Location**: Root directory (`Project/`)

**Available Endpoints**:
- `GET /` - Health check
- `GET /customers/high-risk` - Get all high-risk (churned) customers
- `POST /predict-churn` - Predict churn for a single customer
- `GET /customers` - Get all customers
- `GET /churn-summary` - Get churn statistics

### 2. **React Frontend (Vite)**
- **URL**: `http://localhost:3000`
- **Status**: ✓ Running on port 3000
- **Command**: `npm run dev`
- **Location**: `phase4/`

**Features**:
- High-Risk Customers Dashboard
- Customer Search
- Churn Prediction Form
- Churn Summary Analytics

### 3. **MySQL Database**
- **Host**: `localhost:3306`
- **Database**: `customer_retention`
- **Credentials**: root/root (from `.env`)
- **Status**: ✓ Connected and populated

---

## Data Pipeline Status

### Phase 5 - Data Engineering
✓ **Data Ingestion Complete**:
- CSV loaded: `7,043 customer records`
- Tables populated:
  - `customers`: 7,043 records
  - `contracts`: 7,043 records
  - `billing`: 7,043 records
  - `customer_status`: 7,043 records *(7 1,869 churned, 5,174 retained)*
  - `services`: *Empty (optional for high-risk identification)*

### Phase 6 - ML Models
✓ **Models Available**:
- Decision Tree: `models/tree_churn.pkl`
- Logistic Regression: `models/logistic_churn.pkl`

---

## Key Integration Points

### 1. High-Risk Customers Identification ✓
**Problem Solved**: High-risk customers not showing in UI
**Root Cause**: Services table was empty, causing INNER JOINs to return 0 results
**Solution**: Changed JOIN to LEFT JOIN and made `internet_service` optional in schema

**Result**:
- API now returns: **1,869 high-risk customers**
- Customers with `churn = 1` are properly identified
- Sorted by tenure (oldest customers first)

### 2. Frontend-Backend Connection ✓
- React app calls API at: `http://localhost:8000`
- Uses axios for HTTP requests
- Passes `X-API-Key` header: `mysecret123`
- Environment variables configured in `.env` files

### 3. Database Connection ✓
- SQLAlchemy ORM properly configured
- MySQL connection verified
- All required tables created and populated

---

## How to Use

### Access the Application
1. **Frontend**: Open `http://localhost:3000` in your browser
2. **API Documentation**: Visit `http://localhost:8000/docs` (Swagger UI)
3. **Database**: Connect via MySQL client using `root:root@localhost:3306`

### View High-Risk Customers
1. Navigate to "High-Risk Customers" page in React UI
2. See all 1,869 customers identified as high churn risk
3. View details: Tenure, Monthly Charges, Contract Type, Gender

### Make Predictions
1. Go to "Churn Prediction" page
2. Enter customer details:
   - Tenure (months)
   - Monthly Charges ($)
   - Contract Type (Month-to-month, One year, Two year)
   - Number of Services
3. Get real-time churn risk prediction

### API Examples

**Get High-Risk Customers**:
```bash
curl -X GET "http://localhost:8000/customers/high-risk" \
  -H "X-API-Key: mysecret123"
```

**Predict Churn**:
```bash
curl -X POST "http://localhost:8000/predict-churn" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: mysecret123" \
  -d '{
    "tenure": 10,
    "monthly_charges": 65.5,
    "contract_type": "Month-to-month",
    "service_count": 3
  }'
```

---

## Files Modified for Integration

1. **`routers/high_risk.py`**: Fixed SQL JOIN from INNER to LEFT
2. **`schemas/high_risk.py`**: Made `internet_service` optional
3. **`database/models.py`**: ORM models for all tables
4. **`phase4/src/api.js`**: API client configuration
5. **`phase4/src/pages/HighRiskCustomers.jsx`**: Frontend component

---

## Environment Configuration

### `.env` file
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=customer_retention
API_KEY=mysecret123
DATABASE_URL=mysql+pymysql://root:root@localhost/customer_retention
```

### `phase4/.env` (if needed)
```env
VITE_API_URL=http://localhost:8000
VITE_API_KEY=mysecret123
```

---

## Troubleshooting

### High-Risk Customers Not Showing
- ✓ **FIXED**: Changed SQL JOIN from INNER to LEFT
- ✓ **FIXED**: Made internet_service optional in response schema

### Database Connection Failed
- Verify MySQL is running
- Check `.env` credentials
- Ensure database `customer_retention` exists

### API Returns 500 Error
- Check backend logs in terminal
- Verify all dependencies installed: `pip install -r requirements.txt`
- Ensure database tables created: `python init_db.py`

### Frontend Not Loading Data
- Verify backend API running on port 8000
- Check browser console for CORS errors
- Verify API key in headers matches `.env`

---

## Summary

✅ **Phase 4 (React)** - Frontend dashboard running on :3000
✅ **Phase 5 (Data Engineering)** - Data loaded (7,043 customers)
✅ **Phase 6 (ML)** - Models available and integrated
✅ **Database** - MySQL populated with all customer data
✅ **Integration** - All three phases connected and working

**1,869 high-risk customers identified and displaying in UI**

---

*Setup completed on 2026-08-17*
