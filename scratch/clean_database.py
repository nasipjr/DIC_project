import os
import sys

# Add parent directory to path to import app and models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db

def clean_database():
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        
        print("Recreating all tables...")
        db.create_all()
        
        # Import seed functions from app
        from app import (
            populate_default_settings, 
            check_and_add_discount_column, 
            check_and_add_tax_rate_column, 
            check_and_add_patient_id_column, 
            check_and_add_plain_password_column, 
            ensure_default_admin
        )
        
        print("Populating default settings...")
        populate_default_settings()
        
        print("Checking/adding discount and tax columns...")
        check_and_add_discount_column()
        check_and_add_tax_rate_column()
        check_and_add_patient_id_column()
        check_and_add_plain_password_column()
        
        print("Ensuring default admin account...")
        ensure_default_admin()
        
        print("SUCCESS: Database is now completely clean and reinitialized with default settings and admin!")

if __name__ == "__main__":
    clean_database()
