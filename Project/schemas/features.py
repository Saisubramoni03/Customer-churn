from pydantic import BaseModel, ConfigDict
from typing import Optional


class CustomerFeaturesResponse(BaseModel):
    customer_id: str
    contract_type: str
    monthly_charges: float
    total_charges: float
    internet_service: Optional[str] = None
    payment_method: str
    tenure: int

    model_config = ConfigDict(from_attributes=True)