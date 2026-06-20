from datetime import datetime
from sqlalchemy import func, or_

from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash

from models import db, Patient, Appointment, Treatment, Invoice, Payment, PaymentAllocation
from services.invoice_service import sync_invoice_for_appointment
from services.payment_service import allocate_patient_payments_to_invoices
from utils.constants import TREATMENT_PRICES, TREATMENT_PROCEDURE_TYPES
from utils.auth_helper import role_required


invoices_bp = Blueprint("invoices", __name__)


def get_invoices_context():
    search_query = request.args.get("search", "").strip()
    sort_by = request.args.get("sort", "date")
    order = request.args.get("order", "desc")
    page = request.args.get("page", 1, type=int)
    per_page = 10

    query = Invoice.query.join(Invoice.patient).join(Invoice.appointment)

    if search_query:
        clean_search = search_query
        if search_query.lower().startswith("inv-"):
            clean_search = search_query[4:]

        filter_conds = [
            Patient.first_name.ilike(f"%{search_query}%"),
            Patient.last_name.ilike(f"%{search_query}%"),
            Patient.phone.ilike(f"%{search_query}%"),
            Appointment.status.ilike(f"%{search_query}%")
        ]

        try:
            invoice_id_val = int(clean_search)
            filter_conds.append(Invoice.id == invoice_id_val)
        except ValueError:
            pass

        try:
            appt_id_val = int(search_query)
            filter_conds.append(Invoice.appointment_id == appt_id_val)
        except ValueError:
            pass

        query = query.filter(or_(*filter_conds))

    treatments_count_sub = (
        db.select(func.count(Treatment.id))
        .where(Treatment.appointment_id == Invoice.appointment_id)
        .scalar_subquery()
    )

    total_amount_sub = (
        db.select(func.coalesce(func.sum(Treatment.total_cost), 0.0))
        .where(Treatment.appointment_id == Invoice.appointment_id)
        .scalar_subquery()
    )

    total_paid_sub = (
        db.select(func.coalesce(func.sum(PaymentAllocation.amount), 0.0))
        .where(PaymentAllocation.invoice_id == Invoice.id)
        .scalar_subquery()
    )

    sort_columns = {
        "id": Invoice.id,
        "patient": [Patient.first_name, Patient.last_name],
        "date": Appointment.appointment_date,
        "treatments": treatments_count_sub,
        "total": total_amount_sub,
        "payments": total_paid_sub,
        "outstanding": total_amount_sub - total_paid_sub,
        "status": total_amount_sub - total_paid_sub,
    }

    sort_col = sort_columns.get(sort_by, Appointment.appointment_date)

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
        "invoices": pagination.items,
        "pagination": pagination,
        "search_query": search_query,
        "sort_by": sort_by,
        "order": order,
    }


@invoices_bp.route("/invoices")
@role_required("admin", "doctor", "receptionist")
def invoices():
    current_app.logger.info("Invoices page opened")

    try:
        context = get_invoices_context()
        return render_template("invoices/invoices.html", **context)

    except Exception:
        current_app.logger.exception("Failed to load invoices page")
        return render_template(
            "error_message.html",
            title="Error",
            message="Failed to load invoices.",
            back_url=url_for("dashboard.home"),
        ), 500


@invoices_bp.route("/invoices/table")
@role_required("admin", "doctor", "receptionist")
def invoices_table():
    current_app.logger.info("Invoices table partial requested")

    try:
        context = get_invoices_context()
        return render_template("partials/_invoices_table.html", **context)

    except Exception:
        current_app.logger.exception("Failed to load invoices table")
        return render_template(
            "error_message.html",
            title="Error",
            message="Failed to load invoices table.",
            back_url=url_for("dashboard.home"),
        ), 500
        
@invoices_bp.route("/invoices/add", methods=["GET", "POST"])
@role_required("admin", "receptionist")
def add_invoice():
    current_app.logger.info("Add manual invoice page/request")

    try:
        patients = (
            Patient.query
            .order_by(Patient.first_name.asc(), Patient.last_name.asc())
            .all()
        )

        default_visit_datetime = datetime.now().replace(second=0, microsecond=0)

        if request.method == "POST":
            patient_id = request.form.get("patient_id", type=int)
            appointment_date_raw = request.form.get("appointment_date", "").strip()

            procedure_types = request.form.getlist("procedure_type")
            tooth_numbers = request.form.getlist("tooth_number")
            notes_list = request.form.getlist("notes")

            payment_option = request.form.get("payment_option", "no_payment").strip()
            custom_payment_amount_raw = request.form.get("custom_payment_amount", "").strip()

            patient = Patient.query.get(patient_id)

            if not patient:
                return render_template(
                    "invoices/add_invoice.html",
                    patients=patients,
                    treatment_prices=dict(TREATMENT_PRICES),
                    default_visit_datetime=default_visit_datetime.strftime("%Y-%m-%dT%H:%M"),
                    error_message="Please select a valid patient.",
                ), 400

            if not appointment_date_raw:
                return render_template(
                    "invoices/add_invoice.html",
                    patients=patients,
                    treatment_prices=dict(TREATMENT_PRICES),
                    default_visit_datetime=default_visit_datetime.strftime("%Y-%m-%dT%H:%M"),
                    error_message="Visit date is required.",
                ), 400

            try:
                appointment_date = datetime.strptime(appointment_date_raw, "%Y-%m-%dT%H:%M")
            except ValueError:
                return render_template(
                    "invoices/add_invoice.html",
                    patients=patients,
                    treatment_prices=dict(TREATMENT_PRICES),
                    default_visit_datetime=default_visit_datetime.strftime("%Y-%m-%dT%H:%M"),
                    error_message="Visit date must be valid.",
                ), 400

            invoice_items = []

            for index, procedure_type in enumerate(procedure_types):
                procedure_type = procedure_type.strip()

                if not procedure_type:
                    continue

                if procedure_type not in TREATMENT_PROCEDURE_TYPES:
                    return render_template(
                        "invoices/add_invoice.html",
                        patients=patients,
                        treatment_prices=dict(TREATMENT_PRICES),
                        default_visit_datetime=default_visit_datetime.strftime("%Y-%m-%dT%H:%M"),
                        error_message="Invalid treatment procedure type.",
                    ), 400

                tooth_number = tooth_numbers[index].strip() if index < len(tooth_numbers) else ""
                if len(tooth_number) > 50:
                    return render_template(
                        "invoices/add_invoice.html",
                        patients=patients,
                        treatment_prices=dict(TREATMENT_PRICES),
                        default_visit_datetime=default_visit_datetime.strftime("%Y-%m-%dT%H:%M"),
                        error_message="Tooth number cannot exceed 50 characters.",
                    ), 400
                notes = notes_list[index].strip() if index < len(notes_list) else ""

                invoice_items.append({
                    "procedure_type": procedure_type,
                    "tooth_number": tooth_number,
                    "notes": notes,
                    "total_cost": TREATMENT_PRICES[procedure_type],
                })

            if not invoice_items:
                return render_template(
                    "invoices/add_invoice.html",
                    patients=patients,
                    treatment_prices=dict(TREATMENT_PRICES),
                    default_visit_datetime=default_visit_datetime.strftime("%Y-%m-%dT%H:%M"),
                    error_message="Please add at least one invoice item.",
                ), 400

            appointment = Appointment(
                patient_id=patient.id,
                appointment_date=appointment_date,
                reason="Manual",
                status="Done",
            )

            db.session.add(appointment)
            db.session.flush()

            for item in invoice_items:
                treatment = Treatment(
                    appointment_id=appointment.id,
                    treatment_date=appointment.appointment_date,
                    procedure_type=item["procedure_type"],
                    tooth_number=item["tooth_number"],
                    notes=item["notes"],
                    total_cost=item["total_cost"],
                )

                db.session.add(treatment)

            db.session.flush()

            invoice = sync_invoice_for_appointment(appointment)
            
            discount_type = request.form.get("discount_type", "value").strip()
            if discount_type not in {"value", "percentage"}:
                discount_type = "value"
                
            discount_val = 0.0
            discount_raw = request.form.get("discount", "0").strip()
            if discount_raw:
                try:
                    discount_val = float(discount_raw)
                    if discount_val < 0:
                        discount_val = 0.0
                except ValueError:
                    pass
            
            if discount_type == "percentage" and discount_val > 100.0:
                discount_val = 100.0
            elif discount_type == "value" and discount_val > float(invoice.subtotal):
                discount_val = float(invoice.subtotal)
                
            from decimal import Decimal
            invoice.discount = Decimal(str(discount_val))
            invoice.discount_type = discount_type
            db.session.flush()

            invoice_total = invoice.total_amount

            if payment_option not in {"no_payment", "full_price", "custom_amount"}:
                return render_template(
                    "invoices/add_invoice.html",
                    patients=patients,
                    treatment_prices=dict(TREATMENT_PRICES),
                    default_visit_datetime=default_visit_datetime.strftime("%Y-%m-%dT%H:%M"),
                    error_message="Invalid payment option.",
                ), 400

            payment_amount = 0

            if payment_option == "full_price":
                payment_amount = invoice_total

            elif payment_option == "custom_amount":
                if not custom_payment_amount_raw:
                    return render_template(
                        "invoices/add_invoice.html",
                        patients=patients,
                        treatment_prices=dict(TREATMENT_PRICES),
                        default_visit_datetime=default_visit_datetime.strftime("%Y-%m-%dT%H:%M"),
                        error_message="Custom payment amount is required.",
                    ), 400

                try:
                    payment_amount = float(custom_payment_amount_raw)
                except ValueError:
                    return render_template(
                        "invoices/add_invoice.html",
                        patients=patients,
                        treatment_prices=dict(TREATMENT_PRICES),
                        default_visit_datetime=default_visit_datetime.strftime("%Y-%m-%dT%H:%M"),
                        error_message="Custom payment amount must be a valid number.",
                    ), 400

                if payment_amount <= 0:
                    return render_template(
                        "invoices/add_invoice.html",
                        patients=patients,
                        treatment_prices=dict(TREATMENT_PRICES),
                        default_visit_datetime=default_visit_datetime.strftime("%Y-%m-%dT%H:%M"),
                        error_message="Custom payment amount must be greater than 0.",
                    ), 400

                if payment_amount > invoice_total:
                    return render_template(
                        "invoices/add_invoice.html",
                        patients=patients,
                        treatment_prices=dict(TREATMENT_PRICES),
                        default_visit_datetime=default_visit_datetime.strftime("%Y-%m-%dT%H:%M"),
                        error_message="Custom payment amount cannot be greater than invoice total.",
                    ), 400

            if payment_amount > 0:
                payment = Payment(
                    patient_id=patient.id,
                    amount=payment_amount,
                    notes=f"Manual invoice payment for {invoice.invoice_number}",
                )

                db.session.add(payment)
                db.session.flush()

            allocate_patient_payments_to_invoices(patient.id)

            db.session.commit()

            current_app.logger.info(
                f"Manual invoice created successfully | invoice_id={invoice.id}, patient_id={patient.id}"
            )

            return redirect(url_for("invoices.view_invoice", invoice_id=invoice.id))

        return render_template(
            "invoices/add_invoice.html",
            patients=patients,
            treatment_prices=dict(TREATMENT_PRICES),
            default_visit_datetime=default_visit_datetime.strftime("%Y-%m-%dT%H:%M"),
        )

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to create manual invoice")
        return render_template(
            "error_message.html",
            title="Error",
            message="Failed to create manual invoice.",
            back_url=url_for("invoices.invoices"),
        ), 500


@invoices_bp.route("/invoices/<int:invoice_id>")
@role_required("admin", "doctor", "receptionist")
def view_invoice(invoice_id):
    current_app.logger.info(f"Invoice detail page opened | invoice_id={invoice_id}")

    try:
        invoice = Invoice.query.get_or_404(invoice_id)

        return render_template(
            "invoices/invoice_detail.html",
            invoice=invoice,
            appointment=invoice.appointment,
            patient=invoice.patient,
            treatments=invoice.treatments,
        )

    except Exception:
        current_app.logger.exception(
            f"Failed to load invoice detail | invoice_id={invoice_id}"
        )
        return render_template(
            "error_message.html",
            title="Error",
            message="Failed to load invoice.",
            back_url=url_for("invoices.invoices"),
        ), 500


@invoices_bp.route("/invoices/<int:invoice_id>/discount", methods=["POST"])
@role_required("admin", "receptionist")
def update_invoice_discount(invoice_id):
    current_app.logger.info(f"Update discount request | invoice_id={invoice_id}")
    try:
        invoice = Invoice.query.get_or_404(invoice_id)
        
        discount_type = request.form.get("discount_type", "value").strip()
        if discount_type not in {"value", "percentage"}:
            discount_type = "value"
            
        discount_raw = request.form.get("discount", "0").strip()
        discount_val = 0.0
        if discount_raw:
            try:
                discount_val = float(discount_raw)
                if discount_val < 0:
                    discount_val = 0.0
            except ValueError:
                flash("Invalid discount amount.", "danger")
                return redirect(url_for("invoices.view_invoice", invoice_id=invoice.id))
        
        if discount_type == "percentage" and discount_val > 100.0:
            flash("Discount percentage cannot exceed 100%.", "danger")
            return redirect(url_for("invoices.view_invoice", invoice_id=invoice.id))
        elif discount_type == "value" and discount_val > float(invoice.subtotal):
            flash("Discount cannot exceed the subtotal.", "danger")
            return redirect(url_for("invoices.view_invoice", invoice_id=invoice.id))
            
        from decimal import Decimal
        invoice.discount = Decimal(str(discount_val))
        invoice.discount_type = discount_type
        db.session.flush()
        
        # Recalculate allocations for the patient since invoice total has changed
        allocate_patient_payments_to_invoices(invoice.patient_id)
        db.session.commit()
        
        flash("Discount updated successfully!", "success")
    except Exception:
        db.session.rollback()
        current_app.logger.exception(f"Failed to update discount for invoice {invoice_id}")
        flash("Failed to update discount.", "danger")
        
    return redirect(url_for("invoices.view_invoice", invoice_id=invoice_id))

