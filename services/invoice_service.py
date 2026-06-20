from models import db, Invoice, PaymentAllocation


def get_or_create_invoice_for_appointment(appointment):
    if appointment.invoice:
        return appointment.invoice

    invoice = Invoice(
        appointment_id=appointment.id,
        patient_id=appointment.patient_id,
        tax_rate=0.0
    )

    db.session.add(invoice)
    db.session.flush()

    return invoice


def remove_invoice_if_empty(appointment):
    if not appointment.invoice:
        return

    if appointment.treatments_count > 0:
        return

    PaymentAllocation.query.filter_by(invoice_id=appointment.invoice.id).delete()
    db.session.delete(appointment.invoice)
    db.session.flush()


def sync_invoice_for_appointment(appointment):
    if appointment.treatments_count > 0:
        return get_or_create_invoice_for_appointment(appointment)

    remove_invoice_if_empty(appointment)
    return None