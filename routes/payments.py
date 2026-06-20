from datetime import datetime
from sqlalchemy import func, or_

from flask import Blueprint, current_app, render_template, request, redirect, url_for

from models import db, Patient, Payment, PaymentAllocation
from services.payment_service import allocate_patient_payments_to_invoices
from utils.validators import parse_invoice_payment_amount
from utils.auth_helper import role_required


payments_bp = Blueprint("payments", __name__)


def get_payments_context():
    search_query = request.args.get("search", "").strip()
    sort_by = request.args.get("sort", "date")
    order = request.args.get("order", "desc")
    page = request.args.get("page", 1, type=int)
    per_page = 10

    query = Payment.query.join(Patient)

    if search_query:
        clean_search = search_query
        if search_query.lower().startswith("pay-"):
            clean_search = search_query[4:]

        filter_conds = [
            Patient.first_name.ilike(f"%{search_query}%"),
            Patient.last_name.ilike(f"%{search_query}%"),
            Patient.phone.ilike(f"%{search_query}%"),
            Payment.notes.ilike(f"%{search_query}%")
        ]

        try:
            payment_id_val = int(clean_search)
            filter_conds.append(Payment.id == payment_id_val)
        except ValueError:
            pass

        try:
            amount_val = float(search_query)
            filter_conds.append(Payment.amount == amount_val)
        except ValueError:
            pass

        query = query.filter(or_(*filter_conds))

    allocated_sum = (
        db.select(func.coalesce(func.sum(PaymentAllocation.amount), 0.0))
        .where(PaymentAllocation.payment_id == Payment.id)
        .scalar_subquery()
    )

    sort_columns = {
        "id": Payment.id,
        "date": Payment.payment_date,
        "patient": [Patient.first_name, Patient.last_name],
        "amount": Payment.amount,
        "allocated": allocated_sum,
        "credit": Payment.amount - allocated_sum,
    }

    sort_col = sort_columns.get(sort_by, Payment.payment_date)

    if isinstance(sort_col, list):
        if order == "asc":
            query = query.order_by(*(c.asc() for c in sort_col))
        else:
            query = query.order_by(*(c.desc() for c in sort_col))
    else:
        if order == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())

    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )

    return {
        "payments": pagination.items,
        "pagination": pagination,
        "search_query": search_query,
        "sort_by": sort_by,
        "order": order,
    }


@payments_bp.route("/payments")
@role_required("admin", "receptionist")
def payments():
    current_app.logger.info("Payments page opened")

    try:
        context = get_payments_context()
        return render_template("payments/payments.html", **context)

    except Exception:
        current_app.logger.exception("Failed to load payments page")
        return render_template(
            "error_message.html",
            title="Error",
            message="Failed to load payments.",
            back_url=url_for("dashboard.home"),
        ), 500


@payments_bp.route("/payments/table")
@role_required("admin", "receptionist")
def payments_table():
    current_app.logger.info("Payments table partial requested")

    try:
        context = get_payments_context()
        return render_template("partials/_payments_table.html", **context)

    except Exception:
        current_app.logger.exception("Failed to load payments table")
        return render_template(
            "error_message.html",
            title="Error",
            message="Failed to load payments table.",
            back_url=url_for("dashboard.home"),
        ), 500


@payments_bp.route("/payments/add", methods=["GET", "POST"])
@role_required("admin", "receptionist")
def add_patient_payment():
    current_app.logger.info("Add patient payment page/request")

    try:
        patients = Patient.query.order_by(
            Patient.first_name.asc(),
            Patient.last_name.asc(),
        ).all()

        selected_patient_id = request.args.get("patient_id", type=int)
        invoice_id = request.args.get("invoice_id", type=int)
        selected_patient = None

        if selected_patient_id:
            selected_patient = Patient.query.get(selected_patient_id)

        if request.method == "POST":
            patient_id = request.form.get("patient_id", type=int)
            payment_amount_raw = request.form.get("payment_amount", "")
            notes = request.form.get("notes", "").strip()
            invoice_id = request.form.get("invoice_id", type=int) or invoice_id

            patient = Patient.query.get(patient_id)

            if not patient:
                return render_template(
                    "payments/add_patient_payment.html",
                    patients=patients,
                    selected_patient_id=selected_patient_id,
                    selected_patient=selected_patient,
                    error_message="Please select a valid patient.",
                    invoice_id=invoice_id,
                ), 400

            payment_amount, payment_error = parse_invoice_payment_amount(payment_amount_raw)

            if payment_error:
                return render_template(
                    "payments/add_patient_payment.html",
                    patients=patients,
                    selected_patient_id=patient_id,
                    selected_patient=patient,
                    error_message=payment_error,
                    invoice_id=invoice_id,
                ), 400

            new_payment = Payment(
                patient_id=patient.id,
                amount=payment_amount,
                notes=notes,
            )

            db.session.add(new_payment)
            db.session.flush()

            allocate_patient_payments_to_invoices(patient.id)

            db.session.commit()

            current_app.logger.info(
                f"Patient payment added successfully | patient_id={patient.id}, "
                f"payment_id={new_payment.id}, amount={payment_amount}"
            )

            if invoice_id:
                return redirect(url_for("invoices.view_invoice", invoice_id=invoice_id))
            return redirect(url_for("payments.payments"))

        return render_template(
            "payments/add_patient_payment.html",
            patients=patients,
            selected_patient_id=selected_patient_id,
            selected_patient=selected_patient,
            invoice_id=invoice_id,
        )

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to add patient payment")
        return render_template(
            "error_message.html",
            title="Error",
            message="Failed to add payment.",
            back_url=url_for("payments.payments"),
        ), 500
