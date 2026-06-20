from datetime import datetime, time

from flask import Blueprint, current_app, render_template

from models import db, Patient, Appointment, Treatment, Payment, InventoryItem
from utils.auth_helper import role_required


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@role_required("admin", "doctor", "receptionist")
def home():
    current_app.logger.info("Home page opened")

    try:
        total_patients = Patient.query.count()
        total_appointments = Appointment.query.count()
        scheduled_appointments = Appointment.query.filter_by(status="Scheduled").count()
        done_appointments = Appointment.query.filter_by(status="Done").count()
        total_treatments = Treatment.query.count()
        total_stock_items = InventoryItem.query.count()
        low_stock_count = InventoryItem.query.filter(InventoryItem.quantity < 10).count()

        today = datetime.now().date()
        today_start = datetime.combine(today, time.min)
        today_end = datetime.combine(today, time.max)

        today_scheduled_appointments = (
            Appointment.query
            .join(Patient)
            .filter(Appointment.appointment_date >= today_start)
            .filter(Appointment.appointment_date <= today_end)
            .filter(Appointment.status == "Scheduled")
            .order_by(Appointment.appointment_date.asc())
            .all()
        )

        today_done_appointments = (
            Appointment.query
            .join(Patient)
            .filter(Appointment.appointment_date >= today_start)
            .filter(Appointment.appointment_date <= today_end)
            .filter(Appointment.status == "Done")
            .order_by(Appointment.appointment_date.asc())
            .all()
        )

        from sqlalchemy import func
        total_revenue = db.session.query(func.sum(Treatment.total_cost)).scalar() or 0.0
        total_paid = db.session.query(func.sum(Payment.amount)).scalar() or 0.0

        total_revenue = float(total_revenue)
        total_paid = float(total_paid)
        total_remaining = total_revenue - total_paid
        total_outstanding = max(0.0, total_remaining)
        total_credit = max(0.0, -total_remaining)

        today_payments_sum = db.session.query(func.sum(Payment.amount)).filter(Payment.payment_date >= today_start, Payment.payment_date <= today_end).scalar() or 0.0
        today_revenue_sum = db.session.query(func.sum(Treatment.total_cost)).filter(Treatment.treatment_date >= today_start, Treatment.treatment_date <= today_end).scalar() or 0.0

        today_payments_sum = float(today_payments_sum)
        today_revenue_sum = float(today_revenue_sum)

        pending_appointments = (
            Appointment.query
            .join(Patient)
            .filter(Appointment.status == "Pending")
            .order_by(Appointment.appointment_date.asc())
            .all()
        )

        return render_template(
            "dashboard/index.html",
            total_patients=total_patients,
            total_appointments=total_appointments,
            scheduled_appointments=scheduled_appointments,
            done_appointments=done_appointments,
            total_treatments=total_treatments,
            total_revenue=total_revenue,
            total_paid=total_paid,
            total_remaining=total_remaining,
            total_outstanding=total_outstanding,
            total_credit=total_credit,
            today_scheduled_appointments=today_scheduled_appointments,
            today_done_appointments=today_done_appointments,
            today_payments_sum=today_payments_sum,
            today_revenue_sum=today_revenue_sum,
            pending_appointments=pending_appointments,
            total_stock_items=total_stock_items,
            low_stock_count=low_stock_count,
        )

    except Exception:
        current_app.logger.exception("Error while loading home page")
        return "Error Loading MainPage", 500