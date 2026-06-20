import os
import sys
from datetime import datetime, date, timedelta

# Add parent directory to path to import app and models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db, Patient, Appointment

def insert_dummy_data():
    with app.app_context():
        print("Inserting 10 dummy patients...")
        patients_data = [
            {"first_name": "أحمد", "last_name": "العلي", "phone": "+963958948721", "email": "ahmed.ali@example.com", "date_of_birth": date(1990, 5, 15), "gender": "Male", "city": "دمشق", "address": "المزة"},
            {"first_name": "فاطمة", "last_name": "الحسن", "phone": "+963958948722", "email": "fatima.hassan@example.com", "date_of_birth": date(1995, 8, 20), "gender": "Female", "city": "حلب", "address": "الشهباء"},
            {"first_name": "محمد", "last_name": "المصري", "phone": "+963958948723", "email": "mohammad.masri@example.com", "date_of_birth": date(1988, 12, 10), "gender": "Male", "city": "حمص", "address": "الإنشاءات"},
            {"first_name": "سارة", "last_name": "الخالد", "phone": "+963958948724", "email": "sara.khaled@example.com", "date_of_birth": date(1992, 3, 5), "gender": "Female", "city": "اللاذقية", "address": "المشروع الأول"},
            {"first_name": "خالد", "last_name": "اليوسف", "phone": "+963958948725", "email": "khaled.youssef@example.com", "date_of_birth": date(1985, 7, 25), "gender": "Male", "city": "حماة", "address": "الشريعة"},
            {"first_name": "نور", "last_name": "الخطيب", "phone": "+963958948726", "email": "nour.khatib@example.com", "date_of_birth": date(1998, 10, 18), "gender": "Female", "city": "طرطوس", "address": "الكورنيش"},
            {"first_name": "يوسف", "last_name": "سليمان", "phone": "+963958948727", "email": "youssef.sleiman@example.com", "date_of_birth": date(1991, 1, 30), "gender": "Male", "city": "دمشق", "address": "أبو رمانة"},
            {"first_name": "منى", "last_name": "عبود", "phone": "+963958948728", "email": "mona.abboud@example.com", "date_of_birth": date(1987, 9, 12), "gender": "Female", "city": "السويداء", "address": "طريق قنوات"},
            {"first_name": "سامر", "last_name": "حنا", "phone": "+963958948729", "email": "samer.hanna@example.com", "date_of_birth": date(1983, 4, 22), "gender": "Male", "city": "دمشق", "address": "باب توما"},
            {"first_name": "رشا", "last_name": "الراعي", "phone": "+963958948730", "email": "rasha.raei@example.com", "date_of_birth": date(1994, 11, 2), "gender": "Female", "city": "حمص", "address": "الحمراء"},
        ]
        
        inserted_patients = []
        for p_info in patients_data:
            patient = Patient(**p_info)
            db.session.add(patient)
            inserted_patients.append(patient)
            
        # Commit patients first to get their generated IDs
        db.session.commit()
        print(f"Successfully inserted {len(inserted_patients)} patients.")
        
        print("Inserting 10 scheduled appointments...")
        reasons = ["Check-up", "Cleaning", "Filling", "Root Canal", "Extraction", "Check-up", "Cleaning", "Filling", "Check-up", "Follow-up"]
        
        start_date = datetime.now() + timedelta(days=1)
        for i, patient in enumerate(inserted_patients):
            # Schedule them on subsequent days at 10:00 AM
            app_date = datetime(start_date.year, start_date.month, start_date.day, 10, 0, 0) + timedelta(days=i)
            appointment = Appointment(
                patient_id=patient.id,
                appointment_date=app_date,
                reason=reasons[i % len(reasons)],
                status="Scheduled"
            )
            db.session.add(appointment)
            
        db.session.commit()
        print("Successfully inserted 10 scheduled appointments.")

if __name__ == "__main__":
    insert_dummy_data()
