from sqlalchemy import Column, Integer, String, DECIMAL
from database.database import Base


class Customer(Base):
    __tablename__ = "customers"

    customer_id = Column(String(20), primary_key=True)
    gender = Column(String(10))
    senior_citizen = Column(Integer)
    partner = Column(Integer)
    dependents = Column(Integer)


class Contract(Base):
    __tablename__ = "contracts"

    contract_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(20))
    contract_type = Column(String(30))



class Billing(Base):
    __tablename__ = "billing"

    billing_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(20))
    tenure = Column(Integer)
    paperless_billing = Column(String(10))
    payment_method = Column(String(50))
    monthly_charges = Column(DECIMAL(10, 2))
    total_charges = Column(DECIMAL(10, 2))

class Service(Base):
    __tablename__ = "services"

    service_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(20))
    phone_service = Column(String(10))
    multiple_lines = Column(String(30))
    internet_service = Column(String(30))
    online_security = Column(String(30))
    online_backup = Column(String(30))
    device_protection = Column(String(30))
    tech_support = Column(String(30))
    streaming_tv = Column(String(30))
    streaming_movies = Column(String(30))


class CustomerStatus(Base):
    __tablename__ = "customer_status"

    status_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String(20))
    churn = Column(Integer)
