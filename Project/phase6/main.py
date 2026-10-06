from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .predict import predict_churn


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Customer Churn Prediction API",
    description="API for predicting customer churn risk",
    version="1.0.0"
)


# ============================================================
# REQUEST SCHEMA
# ============================================================

class ChurnRequest(BaseModel):

    tenure: int = Field(
        ...,
        ge=0,
        description="Customer tenure in months"
    )

    monthly_charges: float = Field(
        ...,
        gt=0,
        description="Monthly customer charges"
    )

    contract_type: str = Field(
        ...,
        description="Month-to-month, One year, or Two year"
    )

    service_count: int = Field(
        ...,
        ge=0,
        description="Number of subscribed services"
    )


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():

    return {
        "message": "Customer Churn Prediction API is running"
    }


# ============================================================
# PREDICT CHURN
# ============================================================

@app.post("/predict-churn")
def predict_customer_churn(request: ChurnRequest):

    try:

        # Validate contract
        allowed_contracts = {
            "Month-to-month",
            "One year",
            "Two year"
        }

        if request.contract_type not in allowed_contracts:

            raise HTTPException(
                status_code=400,
                detail=(
                    "contract_type must be one of: "
                    "Month-to-month, One year, Two year"
                )
            )

        # Call real ML model
        result = predict_churn(
            tenure=request.tenure,
            monthly_charges=request.monthly_charges,
            contract_type=request.contract_type,
            service_count=request.service_count
        )

        return result

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )