from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from decimal import Decimal

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="admin", nullable=False)  # 'admin'
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    plain_password = db.Column(db.String(255), nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)


class InventoryItem(db.Model):
    __tablename__ = "inventory_item"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    sku = db.Column(db.String(100), unique=True, nullable=True)
    quantity = db.Column(db.Integer, default=0, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    company = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Invoice(db.Model):
    __tablename__ = "invoice"

    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(255), nullable=False)
    client_phone = db.Column(db.String(50), nullable=True)
    client_address = db.Column(db.String(255), nullable=True)
    issue_date = db.Column(db.DateTime, default=datetime.now, nullable=False)
    
    discount = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    discount_type = db.Column(db.String(20), default="value", nullable=False)  # "value" or "percentage"
    tax_rate = db.Column(db.Numeric(5, 2), default=0.00, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    status = db.Column(db.String(20), default="Unpaid", nullable=False)  # "Paid", "Unpaid"

    items = db.relationship(
        "InvoiceItem",
        backref="invoice",
        lazy=True,
        cascade="all, delete-orphan"
    )

    payment_allocations = db.relationship(
        "PaymentAllocation",
        backref="invoice",
        lazy=True,
        cascade="all, delete-orphan"
    )

    @property
    def total_paid(self):
        return sum((allocation.amount for allocation in self.payment_allocations), Decimal("0.00"))

    @property
    def outstanding_amount(self):
        return max(self.total_amount - self.total_paid, Decimal("0.00"))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def client(self):
        return Client.query.filter_by(name=self.client_name).first()

    @property
    def invoice_number(self):
        return f"INV-{self.id:04d}"

    @property
    def subtotal(self):
        return sum(item.total_price for item in self.items)

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
        sub = Decimal(str(self.subtotal or 0))
        disc_amt = Decimal(str(self.discount_amount or 0))
        net_before_tax = max(sub - disc_amt, Decimal('0.00'))
        tax_pct = Decimal(str(self.tax_rate or 0))
        return (net_before_tax * tax_pct / Decimal('100.00')).quantize(Decimal('0.01'))

    @property
    def calculated_total(self):
        from decimal import Decimal
        sub = Decimal(str(self.subtotal or 0))
        disc_amt = Decimal(str(self.discount_amount or 0))
        tax_amt = Decimal(str(self.tax_amount or 0))
        return max(sub - disc_amt + tax_amt, Decimal('0.00'))


class InvoiceItem(db.Model):
    __tablename__ = "invoice_item"

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(
        db.Integer,
        db.ForeignKey("invoice.id"),
        nullable=False
    )
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    total_price = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'total_price' not in kwargs and 'quantity' in kwargs and 'unit_price' in kwargs:
            from decimal import Decimal
            self.total_price = Decimal(str(kwargs['quantity'])) * Decimal(str(kwargs['unit_price']))


class SystemSetting(db.Model):
    __tablename__ = "system_setting"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Client(db.Model):
    __tablename__ = "client"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    files = db.relationship(
        "ClientFile",
        backref="client",
        lazy=True,
        cascade="all, delete-orphan"
    )

    payments = db.relationship(
        "Payment",
        backref="client",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def total_invoiced(self):
        invoices = Invoice.query.filter_by(client_name=self.name).all()
        return sum((inv.total_amount for inv in invoices), Decimal("0.00"))

    @property
    def total_paid(self):
        return sum((p.amount for p in self.payments), Decimal("0.00"))

    @property
    def balance(self):
        return self.total_invoiced - self.total_paid

    @property
    def credit(self):
        return max(self.total_paid - self.total_invoiced, Decimal("0.00"))

    @property
    def outstanding(self):
        return max(self.total_invoiced - self.total_paid, Decimal("0.00"))


class ClientFile(db.Model):
    __tablename__ = "client_file"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(512), nullable=False)
    file_size = db.Column(db.Integer, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Payment(db.Model):
    __tablename__ = "payment"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(
        db.Integer,
        db.ForeignKey("client.id"),
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def payment_number(self):
        return f"PAY-{self.id:04d}"

    @property
    def allocated_amount(self):
        return sum(allocation.amount for allocation in self.allocations)

    @property
    def unallocated_amount(self):
        unallocated = self.amount - self.allocated_amount
        if unallocated > 0:
            return unallocated
        return 0.0


class PaymentAllocation(db.Model):
    __tablename__ = "payment_allocation"

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)