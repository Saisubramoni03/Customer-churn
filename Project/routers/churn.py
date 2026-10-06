from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.dependencies import get_db

from schemas.churn import ChurnSummaryResponse
from services.churn_service import get_churn_summary

from database.logger import logger

router = APIRouter(
    prefix="/churn",
    tags=["Churn Analytics"]
)


@router.get(
    "/summary",
    response_model=ChurnSummaryResponse
)
def churn_summary(
    db: Session = Depends(get_db)
):
    logger.info("GET /churn/summary")
    return get_churn_summary(db)