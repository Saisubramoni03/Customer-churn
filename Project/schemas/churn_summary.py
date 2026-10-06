from pydantic import BaseModel


class ChurnSummaryResponse(BaseModel):
    total_customers: int
    churned_customers: int
    churn_rate: float