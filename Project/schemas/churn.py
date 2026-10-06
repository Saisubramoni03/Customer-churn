from pydantic import BaseModel


class ContractChurn(BaseModel):
    contract_type: str
    total: int
    churned: int
    churn_rate: float


class InternetChurn(BaseModel):
    internet_service: str
    total: int
    churned: int
    churn_rate: float


class ChurnSummaryResponse(BaseModel):
    total_customers: int
    churned_customers: int
    active_customers: int
    churn_rate: float

    by_contract: list[ContractChurn]
    by_internet_service: list[InternetChurn]