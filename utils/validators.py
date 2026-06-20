from datetime import datetime, timedelta, time

from utils.constants import APPOINTMENT_REASONS, PATIENT_GENDERS


def parse_treatment_money(total_cost_raw, paid_amount_raw):
    total_cost_raw = str(total_cost_raw or "").strip()
    paid_amount_raw = str(paid_amount_raw or "").strip()

    try:
        total_cost = float(total_cost_raw) if total_cost_raw else 0
        paid_amount = float(paid_amount_raw) if paid_amount_raw else 0
    except ValueError:
        return None, None, "Total cost and paid amount must be valid numbers."

    if total_cost < 0:
        return None, None, "Total cost cannot be negative."

    if paid_amount < 0:
        return None, None, "Paid amount cannot be negative."

    if paid_amount > total_cost:
        return None, None, "Paid amount cannot be greater than total cost."

    return total_cost, paid_amount, None


def parse_patient_data(form):
    first_name = form.get("first_name", "").strip()
    last_name = form.get("last_name", "").strip()
    gender = form.get("gender", "").strip()
    date_of_birth_raw = form.get("date_of_birth", "").strip()

    if not first_name:
        return None, "First name is required."
    if len(first_name) > 100:
        return None, "First name cannot exceed 100 characters."

    if not last_name:
        return None, "Last name is required."
    if len(last_name) > 100:
        return None, "Last name cannot exceed 100 characters."

    if not gender:
        return None, "Gender is required."

    if gender not in PATIENT_GENDERS:
        return None, "Invalid gender value."

    if not date_of_birth_raw:
        return None, "Date of birth is required."

    try:
        date_of_birth = datetime.strptime(date_of_birth_raw, "%Y-%m-%d").date()
    except ValueError:
        return None, "Date of birth must be a valid date."

    title = (form.get("title") or "").strip()
    if title and len(title) > 20:
        return None, "Title cannot exceed 20 characters."

    preferred_first_name = (form.get("preferred_first_name") or "").strip()
    if preferred_first_name and len(preferred_first_name) > 100:
        return None, "Preferred first name cannot exceed 100 characters."

    phone = (form.get("phone") or "").strip()
    if phone and len(phone) > 20:
        return None, "Phone number cannot exceed 20 characters."

    email = (form.get("email") or "").strip()
    if email:
        if len(email) > 120:
            return None, "Email address cannot exceed 120 characters."
        if "@" not in email or "." not in email:
            return None, "Invalid email address format."

    address = (form.get("address") or "").strip()
    if address and len(address) > 255:
        return None, "Address cannot exceed 255 characters."

    city = (form.get("city") or "").strip()
    if city and len(city) > 100:
        return None, "City cannot exceed 100 characters."

    state = (form.get("state") or "").strip()
    if state and len(state) > 100:
        return None, "State cannot exceed 100 characters."

    post_code = (form.get("post_code") or "").strip()
    if post_code and len(post_code) > 20:
        return None, "Post code cannot exceed 20 characters."

    country = (form.get("country") or "").strip()
    if country and len(country) > 100:
        return None, "Country cannot exceed 100 characters."

    occupation = (form.get("occupation") or "").strip()
    if occupation and len(occupation) > 150:
        return None, "Occupation cannot exceed 150 characters."

    emergency_contact = (form.get("emergency_contact") or "").strip()
    if emergency_contact and len(emergency_contact) > 150:
        return None, "Emergency contact cannot exceed 150 characters."

    medicare_number = (form.get("medicare_number") or "").strip()
    if medicare_number and len(medicare_number) > 100:
        return None, "Medicare number cannot exceed 100 characters."

    patient_data = {
        "title": title if title else None,
        "first_name": first_name,
        "last_name": last_name,
        "preferred_first_name": preferred_first_name if preferred_first_name else None,
        "date_of_birth": date_of_birth,
        "gender": gender,
        "phone": phone if phone else None,
        "email": email if email else None,
        "address": address if address else None,
        "city": city if city else None,
        "state": state if state else None,
        "post_code": post_code if post_code else None,
        "country": country if country else None,
        "notes": form.get("notes"),
        "medical_information": form.get("medical_information"),
        "appointment_notes": form.get("appointment_notes"),
        "occupation": occupation if occupation else None,
        "emergency_contact": emergency_contact if emergency_contact else None,
        "medicare_number": medicare_number if medicare_number else None,
    }

    return patient_data, None


def parse_appointment_data(form):
    appointment_date_raw = form.get("appointment_date", "").strip()
    reason = form.get("reason", "").strip()

    if not appointment_date_raw:
        return None, "Appointment date and time is required."

    try:
        appointment_date = datetime.strptime(appointment_date_raw, "%Y-%m-%dT%H:%M")
    except ValueError:
        try:
            appointment_date = datetime.strptime(appointment_date_raw, "%Y-%m-%d %H:%M")
        except ValueError:
            return None, "Appointment date and time must be valid."


    from utils.settings_helper import get_setting

    now = datetime.now().replace(second=0, microsecond=0)
    max_appointment_date = now + timedelta(days=30)

    # Load dynamic working days and hours constraints
    working_days = get_setting("working_days", "0,1,2,3,4,6")
    working_days_list = [d.strip() for d in working_days.split(",") if d.strip()]
    
    start_str = get_setting("working_hours_start", "08:00")
    end_str = get_setting("working_hours_end", "18:00")

    try:
        sh, sm = map(int, start_str.split(':'))
        clinic_start_time = time(sh, sm)
    except Exception:
        clinic_start_time = time(8, 0)

    try:
        eh, em = map(int, end_str.split(':'))
        clinic_end_time = time(eh, em)
    except Exception:
        clinic_end_time = time(18, 0)

    if appointment_date < now:
        return None, "Appointment date and time cannot be in the past."

    if appointment_date > max_appointment_date:
        return None, "Appointment date cannot be more than 30 days from today."

    # Validate dynamic working days of the week (0 = Sunday, 6 = Saturday)
    day_str = appointment_date.strftime("%w")
    if day_str not in working_days_list:
        return None, "Clinic is closed on this day (holiday)."

    if appointment_date.time() < clinic_start_time or appointment_date.time() > clinic_end_time:
        return None, f"Appointment time must be between {start_str} and {end_str}."

    if not reason:
        return None, "Appointment reason is required."

    if reason not in APPOINTMENT_REASONS:
        return None, "Invalid appointment reason."

    appointment_data = {
        "appointment_date": appointment_date,
        "reason": reason,
    }

    return appointment_data, None


def get_appointment_datetime_limits():
    now = datetime.now().replace(second=0, microsecond=0)
    max_appointment_date = now + timedelta(days=30)

    return (
        now.strftime("%Y-%m-%dT%H:%M"),
        max_appointment_date.strftime("%Y-%m-%dT%H:%M"),
    )


def parse_payment_amount(payment_amount_raw, remaining_amount):
    payment_amount_raw = str(payment_amount_raw or "").strip()

    if not payment_amount_raw:
        return None, "Payment amount is required."

    try:
        payment_amount = float(payment_amount_raw)
    except ValueError:
        return None, "Payment amount must be a valid number."

    if payment_amount <= 0:
        return None, "Payment amount must be greater than 0."

    if payment_amount > remaining_amount:
        return None, "Payment amount cannot be greater than the remaining amount."

    return payment_amount, None


def parse_invoice_payment_amount(payment_amount_raw):
    payment_amount_raw = str(payment_amount_raw or "").strip()

    if not payment_amount_raw:
        return None, "Payment amount is required."

    try:
        payment_amount = float(payment_amount_raw)
    except ValueError:
        return None, "Payment amount must be a valid number."

    if payment_amount <= 0:
        return None, "Payment amount must be greater than 0."

    return payment_amount, None


def check_appointment_conflict(appointment_date, current_appointment_id=None):
    from models import Appointment
    from datetime import timedelta
    from utils.settings_helper import get_setting

    try:
        duration = int(get_setting("default_appointment_duration", "30"))
    except ValueError:
        duration = 30

    conflict = Appointment.query.filter(
        Appointment.status.in_(["Scheduled", "Pending"]),
        Appointment.appointment_date < appointment_date + timedelta(minutes=duration),
        Appointment.appointment_date > appointment_date - timedelta(minutes=duration)
    )
    if current_appointment_id:
        conflict = conflict.filter(Appointment.id != current_appointment_id)

    return conflict.first()


import threading
booking_lock = threading.Lock()