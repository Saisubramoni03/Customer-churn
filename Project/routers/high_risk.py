from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.dependencies import get_db
from schemas.high_risk import HighRiskCustomerResponse

from database.logger import logger

router = APIRouter(
    prefix="/customers",
    tags=["High Risk Customers"]
)


@router.get(
    "/high-risk",
    response_model=list[HighRiskCustomerResponse]
)
def get_high_risk_customers(
    db: Session = Depends(get_db)
):
    logger.info("GET /customers/high-risk")

    try:
        result = db.execute(
            text("""
                SELECT
                    c.customer_id,
                    c.gender,
                    ct.contract_type,
                    b.tenure,
                    b.monthly_charges,
                    s.internet_service,
                    cs.churn
                FROM customers c
                JOIN contracts ct ON c.customer_id = ct.customer_id
                JOIN billing b ON c.customer_id = b.customer_id
                LEFT JOIN services s ON c.customer_id = s.customer_id
                JOIN customer_status cs ON c.customer_id = cs.customer_id
                WHERE cs.churn = 1
                ORDER BY b.tenure ASC
            """)
        )

        customers = []

        for row in result:
            customers.append({
                "customer_id": row.customer_id,
                "gender": row.gender,
                "contract_type": row.contract_type,
                "tenure": int(row.tenure or 0),
                "monthly_charges": float(row.monthly_charges or 0),
                "internet_service": row.internet_service,
                "churn": row.churn
            })

        return customers

    except SQLAlchemyError:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Database unavailable",
                "status_code": 500
            }
        )