from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.dependencies import get_db
from database.models import CustomerStatus

from schemas.churn_summary import ChurnSummaryResponse

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


@router.get(
    "/churn-summary",
    response_model=ChurnSummaryResponse
)
def get_churn_summary(
    db: Session = Depends(get_db)
):

    total = db.query(func.count(CustomerStatus.customer_id)).scalar()

    churned = (
        db.query(func.count(CustomerStatus.customer_id))
        .filter(CustomerStatus.churn == 1)
        .scalar()
    )

    churn_rate = round((churned / total) * 100, 2)

    return {
        "total_customers": total,
        "churned_customers": churned,
        "churn_rate": churn_rate
    }