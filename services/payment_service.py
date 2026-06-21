from decimal import Decimal
from models import db, Invoice, Payment, PaymentAllocation

def allocate_client_payments_to_invoices(client_id):
    from models import Client
    client = Client.query.get(client_id)
    if not client:
        return

    payments = (
        Payment.query
        .filter_by(client_id=client_id)
        .order_by(Payment.payment_date.asc(), Payment.id.asc())
        .all()
    )

    invoices = (
        Invoice.query
        .filter_by(client_name=client.name)
        .order_by(Invoice.issue_date.asc(), Invoice.id.asc())
        .all()
    )

    payment_ids = [p.id for p in payments]
    if payment_ids:
        PaymentAllocation.query.filter(PaymentAllocation.payment_id.in_(payment_ids)).delete(synchronize_session=False)

    db.session.flush()

    invoice_allocated = {invoice.id: Decimal("0.00") for invoice in invoices}

    for payment in payments:
        remaining_payment_amount = Decimal(str(payment.amount or 0))

        if remaining_payment_amount <= 0:
            continue

        for invoice in invoices:
            invoice_total = Decimal(str(invoice.total_amount or 0))

            if invoice_total <= 0:
                continue

            allocated_to_invoice = invoice_allocated[invoice.id]
            outstanding_amount = invoice_total - allocated_to_invoice

            if outstanding_amount <= 0:
                continue

            allocation_amount = min(remaining_payment_amount, outstanding_amount)

            allocation = PaymentAllocation(
                payment_id=payment.id,
                invoice_id=invoice.id,
                amount=allocation_amount,
            )

            db.session.add(allocation)
            invoice_allocated[invoice.id] += allocation_amount
            remaining_payment_amount -= allocation_amount

            if remaining_payment_amount <= 0:
                break

    db.session.flush()

    # Sync invoice statuses in the database
    for invoice in invoices:
        db.session.expire(invoice, ['payment_allocations'])
        total_paid = sum(alloc.amount for alloc in invoice.payment_allocations)
        if total_paid >= invoice.total_amount:
            invoice.status = "Paid"
        elif total_paid > 0:
            invoice.status = "Partially Paid"
        else:
            invoice.status = "Unpaid"

    db.session.flush()
