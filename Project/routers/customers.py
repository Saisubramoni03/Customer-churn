from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import JSONResponse

from database.dependencies import get_db
from database.models import (
    Customer,
    Contract,
    Billing,
    Service,
    CustomerStatus,
)

from schemas.customer import (
    CustomerResponse,
    CustomerListResponse,
    CustomerProfileResponse,
)

from database.logger import logger

router = APIRouter(
    prefix="/customers",
    tags=["Customers"]
)


# ==========================
# Search Customers
# ==========================
@router.get("/search", response_model=list[CustomerListResponse])
def search_customers(
    gender: Optional[str] = None,
    contract_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    logger.info(
        f"GET /customers/search gender={gender} contract={contract_type}"
    )

    try:
        query = (
            db.query(Customer)
            .join(
                Contract,
                Customer.customer_id == Contract.customer_id
            )
        )

        if gender:
            query = query.filter(Customer.gender == gender)

        if contract_type:
            query = query.filter(
                Contract.contract_type == contract_type
            )

        return query.all()

    except SQLAlchemyError:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Database unavailable",
                "status_code": 500
            }
        )

# ==========================
# List Customers
# ==========================
@router.get("", response_model=list[CustomerListResponse])
def get_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    logger.info(
        f"GET /customers skip={skip} limit={limit}"
    )

    try:
        customers = (
            db.query(Customer)
            .offset(skip)
            .limit(limit)
            .all()
        )

        return customers

    except SQLAlchemyError:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Database unavailable",
                "status_code": 500
            }
        )

# ==========================
# Customer Profile
# ==========================
@router.get(
    "/{customer_id}/profile",
    response_model=CustomerProfileResponse,
)
def get_customer_profile(
    customer_id: str,
    db: Session = Depends(get_db),
):
    logger.info(
        f"GET /customers/{customer_id}/profile"
    )

    try:
        profile = (
            db.query(
                Customer.customer_id,
                Customer.gender,
                Customer.senior_citizen,
                Customer.partner,
                Customer.dependents,
                Contract.contract_type,
                Billing.monthly_charges,
                Billing.total_charges,
                Billing.payment_method,
                Service.internet_service,
                CustomerStatus.churn,
            )
            .join(
                Contract,
                Customer.customer_id == Contract.customer_id,
            )
            .join(
                Billing,
                Customer.customer_id == Billing.customer_id,
            )
            .outerjoin(
                Service,
                Customer.customer_id == Service.customer_id,
            )
            .join(
                CustomerStatus,
                Customer.customer_id == CustomerStatus.customer_id,
            )
            .filter(Customer.customer_id == customer_id)
            .first()
        )

        if profile is None:
            return JSONResponse(
                status_code=404,
                content={
                    "detail": "Customer not found",
                    "status_code": 404
                }
            )

        return profile

    except SQLAlchemyError:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Database unavailable",
                "status_code": 500
            }
        )

# ==========================
# Get Customer by ID
# ==========================
@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
)
def get_customer(
    customer_id: str,
    db: Session = Depends(get_db),
):
    logger.info(
        f"GET /customers/{customer_id}"
    )

    try:
        customer = (
            db.query(Customer)
            .filter(Customer.customer_id == customer_id)
            .first()
        )

        if customer is None:
            return JSONResponse(
                status_code=404,
                content={
                    "detail": "Customer not found",
                    "status_code": 404
                }
            )

        return customer

    except SQLAlchemyError:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Database unavailable",
                "status_code": 500
            }
        )