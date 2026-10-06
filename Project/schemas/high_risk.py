from pydantic import BaseModel, ConfigDict
from typing import Optional


class HighRiskCustomerResponse(BaseModel):
    customer_id: str
    gender: str
    contract_type: str
    tenure: int
    monthly_charges: float
    internet_service: Optional[str] = None
    churn: int

    model_config = ConfigDict(from_attributes=True)