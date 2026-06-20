from functools import wraps
from datetime import datetime, timedelta, time
import json
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app, jsonify
from models import db, Patient, Appointment, User
from utils.settings_helper import get_setting

portal_bp = Blueprint("portal", __name__, url_prefix="/portal")

def flash_message(key, category="danger", **kwargs):
    lang = request.cookies.get('lang', 'en')
    translations = {
        "ar": {
            "login_required": "يرجى تسجيل الدخول للوصول إلى بوابة المرضى.",
            "fields_required": "يرجى إدخال اسم المستخدم وكلمة المرور.",
            "welcome": "مرحباً بك في بوابتك الخاصة، {name}!",
            "invalid_credentials": "اسم المستخدم أو كلمة المرور غير صالحة.",
            "registration_disabled": "التسجيل العام معطل. يرجى التواصل مع موظفي العيادة لإنشاء حسابك.",
            "logged_out": "لقد قمت بتسجيل الخروج من البوابة بنجاح.",
            "all_fields_required": "جميع الحقول مطلوبة.",
            "invalid_date_format": "تنسيق تاريخ ووقت الموعد غير صالح.",
            "past_date": "لا يمكن حجز موعد في الماضي.",
            "advance_date": "لا يمكن حجز موعد قبل أكثر من 30 يوماً.",
            "clinic_closed": "العيادة مغلقة في هذا اليوم.",
            "time_limit": "يجب أن يكون وقت الموعد بين {start} و {end}.",
            "slot_unavailable": "الوقت المحدد لم يعد متاحاً. يرجى اختيار وقت آخر.",
            "booking_success": "تم تقديم طلب الموعد بنجاح! بانتظار تأكيد الموظفين.",
            "booking_failed": "فشل تقديم الطلب. يرجى المحاولة مرة أخرى."
        },
        "en": {
            "login_required": "Please log in to access the patient portal.",
            "fields_required": "Please enter both username and password.",
            "welcome": "Welcome to your portal, {name}!",
            "invalid_credentials": "Invalid username or password.",
            "registration_disabled": "Public registration is disabled. Please contact the clinic staff to set up your account.",
            "logged_out": "You have logged out of the portal.",
            "all_fields_required": "All fields are required.",
            "invalid_date_format": "Invalid appointment date and time format.",
            "past_date": "Appointment cannot be booked in the past.",
            "advance_date": "Appointment cannot be booked more than 30 days in advance.",
            "clinic_closed": "Clinic is closed on this day.",
            "time_limit": "Appointment time must be between {start} and {end}.",
            "slot_unavailable": "Selected slot is no longer available. Please select another time.",
            "booking_success": "Appointment request submitted successfully! Pending staff confirmation.",
            "booking_failed": "Failed to submit request. Please try again."
        }
    }
    msg_tpl = translations.get(lang, translations["en"]).get(key, key)
    flash(msg_tpl.format(**kwargs), category)


def patient_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session or session.get("role") != "patient":
            flash_message("login_required", "danger")
            return redirect(url_for("portal.login"))
        
        # Verify the patient still exists in the database (e.g. in case database was cleared/reseeded)
        patient_id = session.get("patient_id")
        patient = Patient.query.get(patient_id)
        if not patient:
            session.clear()
            flash_message("login_required", "danger")
            return redirect(url_for("portal.login"))
            
        return f(*args, **kwargs)
    return decorated_function


@portal_bp.route("/login", methods=["GET", "POST"])
def login():
    return redirect(url_for("auth.login"))


@portal_bp.route("/register", methods=["GET", "POST"])
def register():
    flash_message("registration_disabled", "danger")
    return redirect(url_for("portal.login"))


@portal_bp.route("/logout")
def logout():
    session.clear()
    flash_message("logged_out", "success")
    return redirect(url_for("portal.login"))


@portal_bp.route("/dashboard")
@patient_login_required
def dashboard():
    patient_id = session.get("patient_id")
    patient = Patient.query.get_or_404(patient_id)
    
    # Fetch patient appointments ordered by date
    appointments = Appointment.query.filter_by(patient_id=patient_id).order_by(Appointment.appointment_date.desc()).all()
    
    from utils.constants import APPOINTMENT_REASONS
    
    return render_template(
        "portal/dashboard.html",
        patient=patient,
        appointments=appointments,
        reasons=list(APPOINTMENT_REASONS)
    )


@portal_bp.route("/book", methods=["GET", "POST"])
@patient_login_required
def book_appointment():
    return redirect(url_for("portal.dashboard"))


@portal_bp.route("/booked-slots")
@patient_login_required
def booked_slots():
    try:
        # Get all occupied slots in the next 30 days
        now = datetime.now()
        limit_date = now + timedelta(days=30)
        
        occupied = Appointment.query.filter(
            Appointment.status.in_(["Scheduled", "Pending", "Done"]),
            Appointment.appointment_date >= now.date(),
            Appointment.appointment_date <= limit_date
        ).all()
        
        slots = [appt.appointment_date.strftime("%Y-%m-%d %H:%M") for appt in occupied]
        return jsonify(slots)
    except Exception:
        return jsonify([]), 500


@portal_bp.route("/events")
@patient_login_required
def portal_events():
    try:
        # Get all occupied slots in the next 30 days
        now = datetime.now()
        limit_date = now + timedelta(days=30)
        
        occupied = Appointment.query.filter(
            Appointment.status.in_(["Scheduled", "Pending", "Done"]),
            Appointment.appointment_date >= now.date(),
            Appointment.appointment_date <= limit_date
        ).all()
        
        events = []
        for appt in occupied:
            start_iso = appt.appointment_date.isoformat()
            end_iso = (appt.appointment_date + timedelta(minutes=30)).isoformat()
            
            events.append({
                "title": "Reserved",
                "start": start_iso,
                "end": end_iso,
                "color": "#6c757d",  # Muted grey color for occupied slot
                "extendedProps": {
                    "status": "Reserved"
                }
            })
            
        return jsonify(events)
    except Exception:
        current_app.logger.exception("Failed to fetch portal calendar events")
        return jsonify([]), 500


@portal_bp.route("/appointments/<int:appointment_id>/cancel", methods=["POST"])
@patient_login_required
def cancel_appointment(appointment_id):
    patient_id = session.get("patient_id")
    appointment = Appointment.query.filter_by(id=appointment_id, patient_id=patient_id).first_or_404()
    
    lang = request.cookies.get('lang', 'en')
    
    if appointment.status not in ["Scheduled", "Pending"]:
        deny_msg = {
            "ar": "لا يمكنك إلغاء المواعيد المكتملة أو الملغاة بالفعل.",
            "en": "You cannot cancel appointments that are already completed or cancelled."
        }.get(lang, "You cannot cancel this appointment.")
        flash(deny_msg, "danger")
        return redirect(url_for("portal.dashboard"))
    
    try:
        old_status = appointment.status
        appointment.status = "Cancelled"
        db.session.commit()
        
        current_app.logger.info(f"Appointment {appointment.id} cancelled by patient {patient_id}")
        
        success_msg = {
            "ar": "تم إلغاء الموعد بنجاح وتم إشعار العيادة.",
            "en": "Appointment cancelled successfully and the clinic has been notified."
        }.get(lang, "Appointment cancelled successfully.")
        flash(success_msg, "success")
        
        # Send Email Notification to the Clinic/Doctor
        clinic_email = get_setting("clinic_email", "")
        if clinic_email:
            from utils.notification_helper import send_smtp_email
            patient = appointment.patient
            formatted_date = appointment.appointment_date.strftime('%Y-%m-%d %I:%M %p')
            
            subject = f"Appointment Cancelled - Patient: {patient.first_name} {patient.last_name}"
            body = (
                f"Dear Doctor,\n\n"
                f"This is an automated notification to inform you that the following appointment has been cancelled by the patient:\n\n"
                f"Patient Name: {patient.first_name} {patient.last_name}\n"
                f"Phone: {patient.phone or 'N/A'}\n"
                f"Appointment Date/Time: {formatted_date}\n"
                f"Reason for appointment: {appointment.reason}\n"
                f"Previous Status: {old_status}\n\n"
                f"This time slot is now open and available for booking on the calendar.\n\n"
                f"Best regards,\nDental Clinic Management System"
            )
            
            import threading
            app = current_app._get_current_object()
            def send_email_async(app_context):
                with app_context:
                    try:
                        send_smtp_email(clinic_email, subject, body)
                    except Exception as ex:
                        app.logger.error(f"Failed to send cancellation notification email to doctor: {ex}")
            
            threading.Thread(target=send_email_async, args=(app.app_context(),), daemon=True).start()
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Failed to cancel appointment {appointment_id}: {e}")
        error_msg = {
            "ar": "حدث خطأ أثناء إلغاء الموعد. يرجى المحاولة مرة أخرى.",
            "en": "An error occurred while cancelling the appointment. Please try again."
        }.get(lang, "An error occurred.")
        flash(error_msg, "danger")
        
    return redirect(url_for("portal.dashboard"))
