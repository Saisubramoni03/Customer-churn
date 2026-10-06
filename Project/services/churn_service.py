from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import JSONResponse

from database.models import (
    CustomerStatus,
    Contract,
    Service
)


def get_churn_summary(db):
    try:
        total = db.query(
            func.count(CustomerStatus.customer_id)
        ).scalar()

        churned = db.query(
            func.count(CustomerStatus.customer_id)
        ).filter(
            CustomerStatus.churn == 1
        ).scalar()

        churn_rate = round(churned * 100 / total, 2)

        contract_stats = (
            db.query(
                Contract.contract_type,
                func.count(CustomerStatus.customer_id).label("total"),
                func.sum(CustomerStatus.churn).label("churned")
            )
            .join(
                CustomerStatus,
                Contract.customer_id == CustomerStatus.customer_id
            )
            .group_by(Contract.contract_type)
            .all()
        )

        by_contract = []

        for row in contract_stats:

            rate = round(
                row.churned * 100 / row.total,
                2
            )

            by_contract.append({
                "contract_type": row.contract_type,
                "total": row.total,
                "churned": int(row.churned),
                "churn_rate": rate
            })

        internet_stats = (
            db.query(
                Service.internet_service,
                func.count(CustomerStatus.customer_id).label("total"),
                func.sum(CustomerStatus.churn).label("churned")
            )
            .join(
                CustomerStatus,
                Service.customer_id == CustomerStatus.customer_id
            )
            .group_by(Service.internet_service)
            .all()
        )

        by_internet = []

        for row in internet_stats:

            rate = round(
                row.churned * 100 / row.total,
                2
            )

            by_internet.append({
                "internet_service": row.internet_service,
                "total": row.total,
                "churned": int(row.churned),
                "churn_rate": rate
            })

        return {
            "total_customers": total,
            "churned_customers": churned,
            "active_customers": total - churned,
            "churn_rate": churn_rate,
            "by_contract": by_contract,
            "by_internet_service": by_internet
        }

    except SQLAlchemyError:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Database unavailable",
                "status_code": 500
            }
        )