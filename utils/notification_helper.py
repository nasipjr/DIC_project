import os
import threading
import time
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from flask import current_app
from models import db, Appointment, Patient, NotificationLog
from utils.settings_helper import get_setting

def send_twilio_sms(to_number, body):
    account_sid = get_setting("twilio_account_sid", "")
    auth_token = get_setting("twilio_auth_token", "")
    from_number = get_setting("twilio_phone_number", "")
    
    if not account_sid or not auth_token or not from_number:
        current_app.logger.info(f"[MOCK SMS] To: {to_number} | Body: {body}")
        return True, "Mock Sent (Credentials not set)"
        
    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=body,
            from_=from_number,
            to=to_number
        )
        return True, f"Sent SID: {message.sid}"
    except Exception as e:
        current_app.logger.error(f"Twilio SMS sending failed: {e}")
        return False, str(e)

def send_twilio_whatsapp(to_number, body):
    account_sid = get_setting("twilio_account_sid", "")
    auth_token = get_setting("twilio_auth_token", "")
    from_number = get_setting("twilio_whatsapp_number", "")
    
    if not account_sid or not auth_token or not from_number:
        current_app.logger.info(f"[MOCK WhatsApp] To: {to_number} | Body: {body}")
        return True, "Mock Sent (Credentials not set)"
        
    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        to_whatsapp = to_number if to_number.startswith("whatsapp:") else f"whatsapp:{to_number}"
        from_whatsapp = from_number if from_number.startswith("whatsapp:") else f"whatsapp:{from_number}"
        
        message = client.messages.create(
            body=body,
            from_=from_whatsapp,
            to=to_whatsapp
        )
        return True, f"Sent SID: {message.sid}"
    except Exception as e:
        current_app.logger.error(f"Twilio WhatsApp sending failed: {e}")
        return False, str(e)

def send_smtp_email(to_email, subject, body):
    smtp_host = get_setting("smtp_host", "smtp.gmail.com")
    smtp_port = get_setting("smtp_port", "587")
    smtp_user = get_setting("smtp_user", "")
    smtp_password = get_setting("smtp_password", "")
    from_email = get_setting("smtp_from_email", "")
    
    if not smtp_user or not smtp_password or not from_email:
        current_app.logger.info(f"[MOCK EMAIL] To: {to_email} | Subject: {subject} | Body: {body}")
        return True, "Mock Sent (Credentials not set)"
        
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        
        server = smtplib.SMTP(smtp_host, int(smtp_port))
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(from_email, [to_email], msg.as_string())
        server.quit()
        return True, "Email sent successfully"
    except Exception as e:
        current_app.logger.error(f"SMTP Email sending failed: {e}")
        return False, str(e)

def process_reminders(app):
    now = datetime.now()
    end_window = now + timedelta(hours=25)
    
    sms_enabled = get_setting("notification_enable_sms", "false").lower() == "true"
    whatsapp_enabled = get_setting("notification_enable_whatsapp", "false").lower() == "true"
    email_enabled = get_setting("notification_enable_email", "false").lower() == "true"
    
    if not (sms_enabled or whatsapp_enabled or email_enabled):
        return
        
    appointments = Appointment.query.filter(
        Appointment.status == "Scheduled",
        Appointment.appointment_date >= now,
        Appointment.appointment_date <= end_window
    ).all()
    
    clinic_name = get_setting("clinic_name", "Clinic")
    
    for appt in appointments:
        time_to_appt = appt.appointment_date - now
        hours_to_appt = time_to_appt.total_seconds() / 3600.0
        
        patient = appt.patient
        if not patient:
            continue
            
        # 24 hours reminder (run between 22 and 25 hours out)
        if 22.0 <= hours_to_appt <= 25.0:
            trigger_reminder(appt, patient, "24h", sms_enabled, whatsapp_enabled, email_enabled, clinic_name)
            
        # 2 hours reminder (run between 1.5 and 2.5 hours out)
        elif 1.5 <= hours_to_appt <= 2.5:
            trigger_reminder(appt, patient, "2h", sms_enabled, whatsapp_enabled, email_enabled, clinic_name)

def trigger_reminder(appt, patient, type_label, sms_enabled, whatsapp_enabled, email_enabled, clinic_name):
    formatted_date = appt.appointment_date.strftime('%Y-%m-%d %I:%M %p')
    
    # SMS
    if sms_enabled and patient.phone:
        type_key = f"sms_{type_label}"
        existing = NotificationLog.query.filter_by(appointment_id=appt.id, type=type_key).first()
        if not existing:
            body = f"Reminder from {clinic_name}: Your appointment is scheduled for {formatted_date}. Please reply to confirm."
            success, msg = send_twilio_sms(patient.phone, body)
            log = NotificationLog(
                appointment_id=appt.id,
                patient_id=patient.id,
                type=type_key,
                channel="sms",
                recipient=patient.phone,
                status="sent" if success else "failed",
                error_message=msg if not success else None
            )
            db.session.add(log)
            db.session.commit()
            
    # WhatsApp
    if whatsapp_enabled and patient.phone:
        type_key = f"whatsapp_{type_label}"
        existing = NotificationLog.query.filter_by(appointment_id=appt.id, type=type_key).first()
        if not existing:
            body = f"Hello {patient.first_name}, this is a reminder from {clinic_name} for your dental appointment on {formatted_date}."
            success, msg = send_twilio_whatsapp(patient.phone, body)
            log = NotificationLog(
                appointment_id=appt.id,
                patient_id=patient.id,
                type=type_key,
                channel="whatsapp",
                recipient=patient.phone,
                status="sent" if success else "failed",
                error_message=msg if not success else None
            )
            db.session.add(log)
            db.session.commit()
            
    # Email
    if email_enabled and patient.email:
        type_key = f"email_{type_label}"
        existing = NotificationLog.query.filter_by(appointment_id=appt.id, type=type_key).first()
        if not existing:
            subject = f"Appointment Reminder - {clinic_name}"
            body = f"Dear {patient.first_name} {patient.last_name},\n\nThis is a friendly reminder from {clinic_name} that you have an upcoming appointment scheduled on {formatted_date}.\n\nIf you need to reschedule, please contact the clinic.\n\nBest regards,\n{clinic_name}"
            success, msg = send_smtp_email(patient.email, subject, body)
            log = NotificationLog(
                appointment_id=appt.id,
                patient_id=patient.id,
                type=type_key,
                channel="email",
                recipient=patient.email,
                status="sent" if success else "failed",
                error_message=msg if not success else None
            )
            db.session.add(log)
            db.session.commit()

def schedule_appointment_reminders(app):
    def run_reminder_loop():
        # wait a bit for app startup
        time.sleep(15)
        while True:
            with app.app_context():
                try:
                    process_reminders(app)
                except Exception as e:
                    app.logger.error(f"Failed to execute appointment reminders process: {e}")
            # check every 5 minutes (300 seconds)
            time.sleep(300)
            
    thread = threading.Thread(target=run_reminder_loop, daemon=True)
    thread.start()
