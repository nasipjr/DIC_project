from datetime import datetime
from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash
from models import db, Invoice, InvoiceItem, InventoryItem
from utils.auth_helper import role_required
from decimal import Decimal
from services.payment_service import allocate_client_payments_to_invoices

invoices_bp = Blueprint("invoices", __name__)


@invoices_bp.route("/invoices")
@role_required("admin")
def invoices():
    current_app.logger.info("Invoices page opened")
    search_query = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "").strip()
    active_range = request.args.get("range", "all").strip().lower()

    query = Invoice.query

    if search_query:
        query = query.filter(
            (Invoice.client_name.ilike(f"%{search_query}%")) |
            (Invoice.client_phone.ilike(f"%{search_query}%"))
        )

    if status_filter:
        query = query.filter(Invoice.status == status_filter)

    # Apply date range filter
    if active_range in ("today", "week", "month"):
        from datetime import datetime, date, timedelta
        today_val = date.today()
        today_start = datetime.combine(today_val, datetime.min.time())
        if active_range == "today":
            query = query.filter(Invoice.issue_date >= today_start)
        elif active_range == "week":
            # Week start on Saturday: Offset = (weekday + 2) % 7
            week_start = today_start - timedelta(days=(today_val.weekday() + 2) % 7)
            query = query.filter(Invoice.issue_date >= week_start)
        elif active_range == "month":
            month_start = datetime(today_val.year, today_val.month, 1)
            query = query.filter(Invoice.issue_date >= month_start)

    invoices_list = query.order_by(Invoice.issue_date.desc()).all()

    return render_template(
        "invoices/invoices.html",
        invoices=invoices_list,
        search_query=search_query,
        status_filter=status_filter,
        active_range=active_range
    )


@invoices_bp.route("/invoices/add", methods=["GET", "POST"])
@role_required("admin")
def add_invoice():
    if request.method == "POST":
        client_name = request.form.get("client_name", "").strip()
        client_phone = request.form.get("client_phone", "").strip()
        client_address = request.form.get("client_address", "").strip()
        
        discount_raw = request.form.get("discount", "0").strip()
        discount_type = request.form.get("discount_type", "value").strip()
        tax_rate_raw = request.form.get("tax_rate", "0").strip()
        status = request.form.get("status", "Unpaid").strip()

        descriptions = request.form.getlist("description")
        quantities = request.form.getlist("quantity")
        unit_prices = request.form.getlist("unit_price")

        if not client_name:
            flash("Client name is required.", "danger")
            return redirect(url_for("invoices.add_invoice"))

        if not descriptions or len(descriptions) == 0:
            flash("At least one invoice item is required.", "danger")
            return redirect(url_for("invoices.add_invoice"))

        try:
            discount = Decimal(discount_raw)
            tax_rate = Decimal(tax_rate_raw)
        except ValueError:
            flash("Invalid discount or tax rate.", "danger")
            return redirect(url_for("invoices.add_invoice"))

        try:
            # Automatically save client details to Client table if it doesn't exist
            if client_name:
                from models import Client
                existing_client = Client.query.filter_by(name=client_name).first()
                if not existing_client:
                    new_client = Client(
                        name=client_name,
                        phone=client_phone,
                        address=client_address
                    )
                    db.session.add(new_client)
                    db.session.flush()

            # Create Invoice first
            invoice = Invoice(
                client_name=client_name,
                client_phone=client_phone,
                client_address=client_address,
                discount=discount,
                discount_type=discount_type,
                tax_rate=tax_rate,
                status=status
            )
            db.session.add(invoice)
            db.session.flush()  # to get invoice.id

            subtotal = Decimal('0.00')

            for i in range(len(descriptions)):
                desc = descriptions[i].strip()
                if not desc:
                    continue

                try:
                    qty = int(quantities[i])
                    price = Decimal(unit_prices[i])
                except (ValueError, IndexError):
                    continue

                total_item_price = Decimal(str(qty)) * price
                subtotal += total_item_price

                invoice_item = InvoiceItem(
                    invoice_id=invoice.id,
                    description=desc,
                    quantity=qty,
                    unit_price=price,
                    total_price=total_item_price
                )
                db.session.add(invoice_item)

                # Deduct inventory stock if name matches exactly (optional convenience feature)
                inv_item = InventoryItem.query.filter_by(name=desc).first()
                if inv_item:
                    inv_item.quantity = max(0, inv_item.quantity - qty)

            # Flush to calculate properties
            db.session.flush()

            # Set total_amount
            invoice.total_amount = invoice.calculated_total
            db.session.flush()

            # If Paid or Partially Paid, dynamically create a payment transaction
            if status in ("Paid", "Partially Paid"):
                from models import Payment, Client
                payment_amount = Decimal("0.00")
                
                if status == "Paid":
                    payment_amount = invoice.total_amount
                elif status == "Partially Paid":
                    amount_paid_raw = request.form.get("amount_paid", "0").strip()
                    try:
                        payment_amount = Decimal(amount_paid_raw)
                    except ValueError:
                        payment_amount = Decimal("0.00")
                    
                    # Validate: if it exceeds total, cap it or change status
                    if payment_amount >= invoice.total_amount:
                        payment_amount = invoice.total_amount
                        invoice.status = "Paid"
                    elif payment_amount <= 0:
                        payment_amount = Decimal("0.00")
                        invoice.status = "Unpaid"
                
                if payment_amount > 0:
                    client_obj = Client.query.filter_by(name=client_name).first()
                    new_payment = Payment(
                        client_id=client_obj.id if client_obj else None,
                        amount=payment_amount,
                        payment_date=invoice.issue_date or datetime.now(),
                        notes=f"دفعة تلقائية للفاتورة {invoice.invoice_number} ({'كاملة' if invoice.status == 'Paid' else 'جزئية'})"
                    )
                    db.session.add(new_payment)
                    db.session.flush()

            from models import Client
            client_obj = Client.query.filter_by(name=client_name).first()
            if client_obj:
                allocate_client_payments_to_invoices(client_obj.id)

            db.session.commit()

            flash(f"Invoice {invoice.invoice_number} created successfully.", "success")
            return redirect(url_for("invoices.view_invoice", invoice_id=invoice.id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(f"Failed to save invoice: {e}")
            flash("Failed to save invoice due to a database error.", "danger")
            return redirect(url_for("invoices.add_invoice"))

    # GET request - load inventory items for autocompletion
    from models import Client
    clients = Client.query.order_by(Client.name.asc()).all()
    inventory = InventoryItem.query.order_by(InventoryItem.name.asc()).all()
    return render_template("invoices/add_invoice.html", inventory=inventory, clients=clients)


@invoices_bp.route("/invoices/<int:invoice_id>")
@role_required("admin")
def view_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    from models import Client
    client = Client.query.filter_by(name=invoice.client_name).first()
    return render_template("invoices/invoice_detail.html", invoice=invoice, client=client)


@invoices_bp.route("/invoices/delete/<int:invoice_id>", methods=["POST"])
@role_required("admin")
def delete_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    num = invoice.invoice_number
    
    from models import Client
    client_obj = Client.query.filter_by(name=invoice.client_name).first()
    
    try:
        db.session.delete(invoice)
        db.session.flush()
        
        if client_obj:
            allocate_client_payments_to_invoices(client_obj.id)
            
        db.session.commit()
        flash(f"Invoice '{num}' has been deleted.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Failed to delete invoice {invoice_id}: {e}")
        flash("Failed to delete invoice due to database error.", "danger")
    return redirect(url_for("invoices.invoices"))


@invoices_bp.route("/invoices/status/<int:invoice_id>", methods=["POST"])
@role_required("admin")
def update_status(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    new_status = request.form.get("status", "Unpaid").strip()
    if new_status in {"Paid", "Unpaid"}:
        try:
            invoice.status = new_status
            db.session.commit()
            flash(f"Invoice status updated to '{new_status}' successfully.", "success")
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(f"Failed to update status for invoice {invoice_id}: {e}")
            flash("Failed to update status.", "danger")
    return redirect(url_for("invoices.view_invoice", invoice_id=invoice.id))
