from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import JSONResponse

from database.dependencies import get_db
from database.models import Billing, Contract, Service

from schemas.features import CustomerFeaturesResponse

from database.logger import logger


router = APIRouter(
    prefix="/features",
    tags=["Customer Features"]
)


@router.get(
    "/{customer_id}",
    response_model=CustomerFeaturesResponse
)
def get_customer_features(
    customer_id: str,
    db: Session = Depends(get_db)
):
    logger.info(
        f"GET /features/{customer_id}"
    )
    try:
        features = (
            db.query(
                Billing.customer_id,
                Contract.contract_type,
                Billing.monthly_charges,
                Billing.total_charges,
                Billing.payment_method,
                Service.internet_service,
                Billing.tenure
            )
            .join(
                Contract,
                Billing.customer_id == Contract.customer_id
            )
            .outerjoin(
                Service,
                Billing.customer_id == Service.customer_id
            )
            .filter(Billing.customer_id == customer_id)
            .first()
        )

        if features is None:
            return JSONResponse(
        status_code=404,
        content={
            "detail": "Customer not found",
            "status_code": 404
        }
    )

        return features

    except SQLAlchemyError:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Database unavailable",
                "status_code": 500
            }
        )
        