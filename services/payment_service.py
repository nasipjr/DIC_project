from models import db, Appointment, Invoice, Payment, PaymentAllocation


def allocate_patient_payments_to_invoices(patient_id):
    payments = (
        Payment.query
        .filter_by(patient_id=patient_id)
        .order_by(Payment.payment_date.asc(), Payment.id.asc())
        .all()
    )

    invoices = (
        Invoice.query
        .join(Invoice.appointment)
        .filter(Invoice.patient_id == patient_id)
        .order_by(Appointment.appointment_date.asc(), Invoice.id.asc())
        .all()
    )

    payment_ids = [p.id for p in payments]
    if payment_ids:
        PaymentAllocation.query.filter(PaymentAllocation.payment_id.in_(payment_ids)).delete(synchronize_session=False)

    db.session.flush()

    invoice_allocated = {invoice.id: 0.0 for invoice in invoices}

    for payment in payments:
        remaining_payment_amount = float(payment.amount or 0)

        if remaining_payment_amount <= 0:
            continue

        for invoice in invoices:
            invoice_total = float(invoice.total_amount or 0)

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