from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from typing import Optional


class CustomerResponse(BaseModel):
    customer_id: str
    gender: str
    senior_citizen: int
    partner: int
    dependents: int

    model_config = ConfigDict(from_attributes=True)


class CustomerListResponse(BaseModel):
    customer_id: str
    gender: str
    senior_citizen: int
    partner: int
    dependents: int

    model_config = ConfigDict(from_attributes=True)


class CustomerProfileResponse(BaseModel):
    customer_id: str
    gender: str
    senior_citizen: int
    partner: int
    dependents: int

    contract_type: str

    monthly_charges: Decimal
    total_charges: Decimal | None

    internet_service: Optional[str] = None
    payment_method: str

    churn: int

    model_config = ConfigDict(from_attributes=True)