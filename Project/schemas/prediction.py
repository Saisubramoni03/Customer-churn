from pydantic import BaseModel, Field


class ChurnPredictionRequest(BaseModel):
    customer_id: str | None = None

    tenure: int = Field(..., ge=0, le=100)

    monthly_charges: float = Field(..., gt=0)

    contract_type: str

    service_count: int = Field(..., ge=0)


class ChurnPredictionResponse(BaseModel):
    customer_id: str
    risk_score: float
    prediction: str
    confidence: float