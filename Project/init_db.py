#!/usr/bin/env python3
"""
Initialize the database by creating all tables
"""
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.database import engine, Base
from database.models import Customer, Contract, Billing, Service, CustomerStatus

def init_database():
    """Create all tables in the database"""
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        return False

if __name__ == "__main__":
    init_database()
