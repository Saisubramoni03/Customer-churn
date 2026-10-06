from database.database import SessionLocal
from database.models import Customer

db = SessionLocal()

try:
    customers = db.query(Customer).limit(5).all()

    for customer in customers:
        print(
            customer.customer_id,
            customer.gender,
            customer.partner,
            customer.dependents
        )

finally:
    db.close()