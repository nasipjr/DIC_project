from datetime import datetime
from sqlalchemy import func, or_
from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash
from models import db, Client, Payment, PaymentAllocation
from services.payment_service import allocate_client_payments_to_invoices
from utils.auth_helper import role_required
from utils.translations import TRANSLATIONS
from decimal import Decimal, InvalidOperation

payments_bp = Blueprint("payments", __name__)

def flash_translated(key, category="success"):
    lang = request.cookies.get('lang', 'ar')
    item = TRANSLATIONS.get(key)
    msg = item.get(lang, item.get('ar', key)) if item else key
    flash(msg, category)

def get_payments_context():
    search_query = request.args.get("search", "").strip()
    sort_by = request.args.get("sort", "date")
    order = request.args.get("order", "desc")
    page = request.args.get("page", 1, type=int)
    active_range = request.args.get("range", "all").strip().lower()
    per_page = 10

    query = Payment.query.join(Client)

    # Apply date range filter
    if active_range in ("today", "week", "month"):
        from datetime import datetime, date, timedelta
        today_val = date.today()
        today_start = datetime.combine(today_val, datetime.min.time())
        if active_range == "today":
            query = query.filter(Payment.payment_date >= today_start)
        elif active_range == "week":
            # Week start on Saturday: Offset = (weekday + 2) % 7
            week_start = today_start - timedelta(days=(today_val.weekday() + 2) % 7)
            query = query.filter(Payment.payment_date >= week_start)
        elif active_range == "month":
            month_start = datetime(today_val.year, today_val.month, 1)
            query = query.filter(Payment.payment_date >= month_start)

    if search_query:
        clean_search = search_query
        if search_query.lower().startswith("pay-"):
            clean_search = search_query[4:]

        filter_conds = [
            Client.name.ilike(f"%{search_query}%"),
            Client.phone.ilike(f"%{search_query}%"),
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

    sort_columns = {
        "id": Payment.id,
        "date": Payment.payment_date,
        "client": Client.name,
        "amount": Payment.amount
    }

    sort_col = sort_columns.get(sort_by, Payment.payment_date)

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
        "active_range": active_range
    }

@payments_bp.route("/payments")
@role_required("admin")
def payments():
    current_app.logger.info("Payments page opened")
    try:
        context = get_payments_context()
        return render_template("payments/payments.html", **context)
    except Exception as e:
        current_app.logger.exception(f"Failed to load payments page: {e}")
        flash("Failed to load payments.", "danger")
        return redirect(url_for("dashboard.home"))

@payments_bp.route("/payments/table")
@role_required("admin")
def payments_table():
    try:
        context = get_payments_context()
        return render_template("partials/_payments_table.html", **context)
    except Exception as e:
        current_app.logger.exception(f"Failed to load payments table partial: {e}")
        return "Failed to load table.", 500

@payments_bp.route("/payments/add", methods=["GET", "POST"])
@role_required("admin")
def add_payment():
    clients = Client.query.order_by(Client.name.asc()).all()
    selected_client_id = request.args.get("client_id", type=int)
    invoice_id = request.args.get("invoice_id", type=int)
    
    selected_client = None
    if selected_client_id:
        selected_client = Client.query.get(selected_client_id)

    if request.method == "POST":
        client_id = request.form.get("client_id", type=int)
        amount_raw = request.form.get("amount", "").strip()
        notes = request.form.get("notes", "").strip()
        payment_date_raw = request.form.get("payment_date", "").strip()
        
        client = Client.query.get(client_id)
        if not client:
            flash_translated("client_not_found", "danger")
            return render_template(
                "payments/add_payment.html",
                clients=clients,
                selected_client_id=selected_client_id,
                selected_client=selected_client,
                invoice_id=invoice_id
            )

        try:
            amount = Decimal(amount_raw)
            if amount <= 0:
                raise ValueError()
        except (ValueError, InvalidOperation):
            flash("Amount must be a positive number.", "danger")
            return render_template(
                "payments/add_payment.html",
                clients=clients,
                selected_client_id=client_id,
                selected_client=client,
                invoice_id=invoice_id
            )

        payment_date = datetime.now()
        if payment_date_raw:
            try:
                payment_date = datetime.strptime(payment_date_raw, "%Y-%m-%d")
            except ValueError:
                pass

        try:
            new_payment = Payment(
                client_id=client.id,
                amount=amount,
                payment_date=payment_date,
                notes=notes
            )
            db.session.add(new_payment)
            db.session.flush()

            allocate_client_payments_to_invoices(client.id)
            db.session.commit()

            flash_translated("payment_recorded_success", "success")
            
            if invoice_id:
                return redirect(url_for("invoices.view_invoice", invoice_id=invoice_id))
            return redirect(url_for("payments.payments"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(f"Failed to record payment: {e}")
            flash("Failed to save payment due to database error.", "danger")

    return render_template(
        "payments/add_payment.html",
        clients=clients,
        selected_client_id=selected_client_id,
        selected_client=selected_client,
        invoice_id=invoice_id
    )

@payments_bp.route("/payments/<int:payment_id>")
@role_required("admin")
def view_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    return render_template("payments/payment_detail.html", payment=payment)


@payments_bp.route("/payments/<int:payment_id>/delete", methods=["POST"])
@role_required("admin")
def delete_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    client_id = payment.client_id
    try:
        db.session.delete(payment)
        db.session.flush()

        allocate_client_payments_to_invoices(client_id)
        db.session.commit()
        flash_translated("payment_deleted_success", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Failed to delete payment: {e}")
        flash("Failed to delete payment.", "danger")

    return redirect(request.referrer or url_for("payments.payments"))
