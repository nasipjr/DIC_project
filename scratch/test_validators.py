import sys
from datetime import datetime

# Add root folder to path to import helpers
sys.path.append('.')

from utils.validators import parse_patient_data

# Mock form data
valid_form = {
    "first_name": "John",
    "last_name": "Doe",
    "gender": "Male",
    "date_of_birth": "1990-01-01",
    "phone": "+963958948727",
    "email": "john.doe@example.com",
    "address": "Damascus",
    "city": "Damascus",
    "state": "Damascus",
    "post_code": "1234",
    "country": "Syria",
    "title": "Mr",
    "preferred_first_name": "Johnny",
    "occupation": "Engineer",
    "emergency_contact": "Jane Doe",
    "medicare_number": "11223344"
}

print("1. Testing valid form data...")
data, err = parse_patient_data(valid_form)
if err:
    print(f"FAILED: {err}")
else:
    print(f"SUCCESS: parsed data={data}")

print("\n2. Testing invalid phone length (>20)...")
invalid_phone_form = valid_form.copy()
invalid_phone_form["phone"] = "123456789012345678901"
data, err = parse_patient_data(invalid_phone_form)
if err:
    print(f"SUCCESS: Caught expected error: {err}")
else:
    print("FAILED: Did not catch too long phone number")

print("\n3. Testing invalid email format...")
invalid_email_form = valid_form.copy()
invalid_email_form["email"] = "invalidemail"
data, err = parse_patient_data(invalid_email_form)
if err:
    print(f"SUCCESS: Caught expected error: {err}")
else:
    print("FAILED: Did not catch invalid email")

print("\n4. Testing invalid first name length (>100)...")
invalid_name_form = valid_form.copy()
invalid_name_form["first_name"] = "A" * 101
data, err = parse_patient_data(invalid_name_form)
if err:
    print(f"SUCCESS: Caught expected error: {err}")
else:
    print("FAILED: Did not catch too long first name")
