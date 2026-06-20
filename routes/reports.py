from datetime import datetime
from flask import Blueprint, render_template, current_app
from sqlalchemy import func
from sqlalchemy.orm import subqueryload
from utils.auth_helper import role_required

from models import db, Patient, Appointment, Treatment, Payment, PaymentAllocation, Invoice

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/reports")
@role_required("admin")
def reports_dashboard():
    current_app.logger.info("Reports dashboard page opened")

    try:
        # 1. KPI Cards Data
        total_patients = Patient.query.count()
        total_appointments = Appointment.query.count()
        total_invoiced = float(db.session.query(func.sum(Treatment.total_cost)).scalar() or 0.0)
        total_payments = float(db.session.query(func.sum(Payment.amount)).scalar() or 0.0)
        total_outstanding = max(0.0, total_invoiced - total_payments)
        total_credit = max(0.0, total_payments - total_invoiced)

        # 2. Last 6 Months Income (Billed vs Paid) - DB Agnostic Python Logic
        today = datetime.now()
        months = []
        for i in range(5, -1, -1):
            year = today.year
            month = today.month - i
            if month <= 0:
                month += 12
                year -= 1
            months.append((year, month, datetime(year, month, 1)))

        monthly_labels = [m[2].strftime("%B %Y") for m in months]
        monthly_billed = []
        monthly_paid = []

        for year, month, date_start in months:
            if month == 12:
                date_end = datetime(year + 1, 1, 1)
            else:
                date_end = datetime(year, month + 1, 1)

            billed_month = db.session.query(func.sum(Treatment.total_cost)).filter(
                Treatment.treatment_date >= date_start,
                Treatment.treatment_date < date_end
            ).scalar() or 0.0
            monthly_billed.append(float(billed_month))

            paid_month = db.session.query(func.sum(Payment.amount)).filter(
                Payment.payment_date >= date_start,
                Payment.payment_date < date_end
            ).scalar() or 0.0
            monthly_paid.append(float(paid_month))

        # 3. Appointment Status Counts
        status_counts = db.session.query(
            Appointment.status, func.count(Appointment.id)
        ).group_by(Appointment.status).all()

        appointment_statuses = {"Scheduled": 0, "Done": 0, "Cancelled": 0}
        for status, count in status_counts:
            if status in appointment_statuses:
                appointment_statuses[status] = count

        appointment_status_labels = list(appointment_statuses.keys())
        appointment_status_values = list(appointment_statuses.values())

        # 4. Top 5 Procedures
        procedure_counts = db.session.query(
            Treatment.procedure_type,
            func.count(Treatment.id),
            func.sum(Treatment.total_cost)
        ).group_by(Treatment.procedure_type).order_by(func.count(Treatment.id).desc()).limit(5).all()

        procedure_labels = [p[0] for p in procedure_counts]
        procedure_values_counts = [p[1] for p in procedure_counts]
        procedure_values_revenue = [float(p[2] or 0.0) for p in procedure_counts]

        # 5. Patient Gender Demographics
        gender_counts = db.session.query(
            Patient.gender, func.count(Patient.id)
        ).group_by(Patient.gender).all()

        gender_labels = [g[0] or "Not Specified" for g in gender_counts]
        gender_values = [g[1] for g in gender_counts]

        # 6. Top Debtors (Outstanding Debt per Patient)
        all_patients = Patient.query.options(
            subqueryload(Patient.invoices).subqueryload(Invoice.appointment).subqueryload(Appointment.treatments),
            subqueryload(Patient.payments)
        ).all()
        debtors = [
            {
                "id": p.id,
                "name": f"{p.first_name} {p.last_name}",
                "phone": p.phone or "No phone",
                "total_billed": p.total_invoice_amount,
                "total_paid": p.total_payments_amount,
                "outstanding": p.outstanding_amount
            }
            for p in all_patients
            if p.outstanding_amount > 0
        ]
        top_debtors = sorted(debtors, key=lambda x: x["outstanding"], reverse=True)[:5]

        return render_template(
            "reports/reports.html",
            total_patients=total_patients,
            total_appointments=total_appointments,
            total_invoiced=total_invoiced,
            total_payments=total_payments,
            total_outstanding=total_outstanding,
            total_credit=total_credit,
            monthly_labels=monthly_labels,
            monthly_billed=monthly_billed,
            monthly_paid=monthly_paid,
            appointment_status_labels=appointment_status_labels,
            appointment_status_values=appointment_status_values,
            procedure_labels=procedure_labels,
            procedure_values_counts=procedure_values_counts,
            procedure_values_revenue=procedure_values_revenue,
            gender_labels=gender_labels,
            gender_values=gender_values,
            top_debtors=top_debtors
        )

    except Exception:
        current_app.logger.exception("Failed to generate reports dashboard data")
        return render_template(
            "error_message.html",
            title="Error",
            message="Failed to load reports dashboard.",
        ), 500
