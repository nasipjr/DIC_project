from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Patient(db.Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(20))
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)

    preferred_first_name = db.Column(db.String(100))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(20))

    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))

    address = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    post_code = db.Column(db.String(20))
    country = db.Column(db.String(100))

    notes = db.Column(db.Text)
    medical_information = db.Column(db.Text)
    appointment_notes = db.Column(db.Text)

    occupation = db.Column(db.String(150))
    emergency_contact = db.Column(db.String(150))
    medicare_number = db.Column(db.String(100))

    appointments = db.relationship(
        "Appointment",
        backref="patient",
        lazy=True,
    )

    payments = db.relationship(
        "Payment",
        backref="patient",
        lazy=True,
    )

    invoices = db.relationship(
        "Invoice",
        backref="patient",
        lazy=True,
    )

    files = db.relationship(
        "PatientFile",
        backref="patient",
        lazy=True,
        cascade="all, delete-orphan"
    )

    @property
    def treatments(self):
        patient_treatments = []

        for appointment in self.appointments:
            patient_treatments.extend(appointment.treatments)

        return patient_treatments

    @property
    def invoice_appointments(self):
        return [
            invoice.appointment
            for invoice in self.invoices
            if invoice.appointment is not None
        ]

    @property
    def total_invoice_amount(self):
        return sum(invoice.total_amount for invoice in self.invoices)

    @property
    def total_payments_amount(self):
        return sum(payment.amount for payment in self.payments)

    @property
    def total_allocated_amount(self):
        return sum(payment.allocated_amount for payment in self.payments)

    @property
    def outstanding_amount(self):
        balance = self.total_invoice_amount - self.total_payments_amount

        if balance > 0:
            return balance

        return 0

    @property
    def credit_amount(self):
        credit = self.total_payments_amount - self.total_invoice_amount

        if credit > 0:
            return credit

        return 0

    @property
    def balance_amount(self):
        return self.total_invoice_amount - self.total_payments_amount


class Appointment(db.Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patient.id"),
        nullable=False
    )

    appointment_date = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.String(255))
    status = db.Column(db.String(50), default="Scheduled")

    treatments = db.relationship(
        "Treatment",
        backref="appointment",
        lazy=True,
        cascade="all, delete-orphan"
    )

    invoice = db.relationship(
        "Invoice",
        backref="appointment",
        lazy=True,
        uselist=False,
        cascade="all, delete-orphan"
    )

    @property
    def invoice_total(self):
        if self.invoice:
            return self.invoice.total_amount

        return sum(treatment.total_cost for treatment in self.treatments)

    @property
    def total_paid(self):
        if self.invoice:
            return self.invoice.total_paid

        return 0

    @property
    def outstanding_amount(self):
        if self.invoice:
            return self.invoice.outstanding_amount

        total = self.invoice_total

        if total > 0:
            return total

        return 0

    @property
    def balance(self):
        if self.invoice:
            return self.invoice.balance

        return self.invoice_total

    @property
    def credit(self):
        if self.invoice:
            return self.invoice.credit

        return 0

    @property
    def treatments_count(self):
        return len(self.treatments)

    @property
    def has_invoice(self):
        return self.invoice is not None

    @property
    def invoice_status(self):
        if self.invoice:
            return self.invoice.status

        return "No Invoice"

    @property
    def payment_allocations(self):
        if self.invoice:
            return self.invoice.payment_allocations

        return []


class Treatment(db.Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    id = db.Column(db.Integer, primary_key=True)

    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey("appointment.id"),
        nullable=False
    )

    treatment_date = db.Column(db.DateTime, nullable=False)
    procedure_type = db.Column(db.String(200))
    tooth_number = db.Column(db.String(50))
    notes = db.Column(db.Text)

    total_cost = db.Column(db.Numeric(10, 2), default=0.00)

    @property
    def patient(self):
        return self.appointment.patient

    @property
    def patient_id(self):
        return self.appointment.patient_id


class Invoice(db.Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    id = db.Column(db.Integer, primary_key=True)

    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey("appointment.id"),
        nullable=False,
        unique=True
    )

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patient.id"),
        nullable=False
    )

    issue_date = db.Column(db.DateTime, default=datetime.now, nullable=False)
    discount = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    discount_type = db.Column(db.String(20), default="value", nullable=False)
    tax_rate = db.Column(db.Numeric(5, 2), default=0.00, nullable=False)

    payment_allocations = db.relationship(
        "PaymentAllocation",
        backref="invoice",
        lazy=True,
        cascade="all, delete-orphan"
    )

    @property
    def invoice_number(self):
        return f"INV-{self.id}"

    @property
    def treatments(self):
        if not self.appointment:
            return []

        return self.appointment.treatments

    @property
    def appointment_date(self):
        if not self.appointment:
            return None

        return self.appointment.appointment_date

    @property
    def subtotal(self):
        return sum(treatment.total_cost for treatment in self.treatments)

    @property
    def discount_amount(self):
        from decimal import Decimal
        sub = Decimal(str(self.subtotal or 0))
        disc = Decimal(str(self.discount or 0))
        if self.discount_type == "percentage":
            return (sub * disc / Decimal('100.00')).quantize(Decimal('0.01'))
        return disc

    @property
    def tax_amount(self):
        from decimal import Decimal
        return Decimal('0.00')

    @property
    def total_amount(self):
        from decimal import Decimal
        sub = Decimal(str(self.subtotal or 0))
        disc_amt = Decimal(str(self.discount_amount or 0))
        net = max(sub - disc_amt, Decimal('0.00'))
        return net

    @property
    def total_paid(self):
        return sum(allocation.amount for allocation in self.payment_allocations)

    @property
    def outstanding_amount(self):
        balance = self.total_amount - self.total_paid

        if balance > 0:
            return balance

        return 0

    @property
    def balance(self):
        return self.total_amount - self.total_paid

    @property
    def credit(self):
        credit = self.total_paid - self.total_amount

        if credit > 0:
            return credit

        return 0

    @property
    def treatments_count(self):
        return len(self.treatments)

    @property
    def status(self):
        if self.total_paid <= 0:
            return "Unpaid"

        if self.total_paid < self.total_amount:
            return "Partially Paid"

        if self.total_paid == self.total_amount:
            return "Paid"

        return "Credit"


class Payment(db.Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    id = db.Column(db.Integer, primary_key=True)

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patient.id"),
        nullable=False
    )

    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.now, nullable=False)
    notes = db.Column(db.Text)

    allocations = db.relationship(
        "PaymentAllocation",
        backref="payment",
        lazy=True,
        cascade="all, delete-orphan"
    )

    @property
    def allocated_amount(self):
        return sum(allocation.amount for allocation in self.allocations)

    @property
    def unallocated_amount(self):
        unallocated = self.amount - self.allocated_amount

        if unallocated > 0:
            return unallocated

        return 0


class PaymentAllocation(db.Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    id = db.Column(db.Integer, primary_key=True)

    payment_id = db.Column(
        db.Integer,
        db.ForeignKey("payment.id"),
        nullable=False
    )

    invoice_id = db.Column(
        db.Integer,
        db.ForeignKey("invoice.id"),
        nullable=False
    )

    amount = db.Column(db.Numeric(10, 2), nullable=False)

    @property
    def appointment(self):
        return self.invoice.appointment

    @property
    def appointment_id(self):
        return self.invoice.appointment_id

    @property
    def patient(self):
        return self.invoice.patient

    @property
    def patient_id(self):
        return self.invoice.patient_id


class SystemSetting(db.Model):
    __tablename__ = "system_setting"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="receptionist", nullable=False)  # 'admin', 'doctor', 'receptionist', 'patient'
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=True)
    patient = db.relationship("Patient", backref=db.backref("user", uselist=False))
    plain_password = db.Column(db.String(255), nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)


class PatientFile(db.Model):
    __tablename__ = "patient_file"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patient.id"),
        nullable=False
    )
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    filetype = db.Column(db.String(100))
    upload_date = db.Column(db.DateTime, default=datetime.now, nullable=False)
    notes = db.Column(db.Text)
    category = db.Column(db.String(100), default="General", nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class NotificationLog(db.Model):
    __tablename__ = "notification_log"

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(
        db.Integer,
        db.ForeignKey("appointment.id", ondelete="CASCADE"),
        nullable=False
    )
    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patient.id", ondelete="CASCADE"),
        nullable=False
    )
    type = db.Column(db.String(50), nullable=False)
    channel = db.Column(db.String(20), nullable=False)
    recipient = db.Column(db.String(100), nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    status = db.Column(db.String(20), default="sent", nullable=False)
    error_message = db.Column(db.Text)

    appointment = db.relationship(
        "Appointment",
        backref=db.backref("notifications", cascade="all, delete-orphan")
    )
    patient = db.relationship(
        "Patient",
        backref=db.backref("notifications", cascade="all, delete-orphan")
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class InventoryItem(db.Model):
    __tablename__ = "inventory_item"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    sku = db.Column(db.String(100), unique=True, nullable=True)
    quantity = db.Column(db.Integer, default=0, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    description = db.Column(db.Text, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


# Aliases for domain readability
Client = Patient
Service = Treatment
ClientFile = PatientFile
