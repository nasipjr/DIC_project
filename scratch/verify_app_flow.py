import sys
import os

# Add parent directory to path to import app and models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db, User, InventoryItem, Invoice, InvoiceItem

client = app.test_client()

print("Simulating admin login session...")
with app.app_context():
    admin_user = User.query.filter_by(role="admin").first()
    if not admin_user:
        print("Admin user not found. Seeding database first...")
        from app import ensure_default_admin
        ensure_default_admin()
        admin_user = User.query.filter_by(role="admin").first()

with client:
    with client.session_transaction() as sess:
        sess["user_id"] = admin_user.id
        sess["role"] = admin_user.role

    # 1. Add Stock Item
    print("Adding a stock item...")
    res = client.post("/stock/add", data={
        "name": "أنابيب 16 ملم",
        "sku": "PIP-16",
        "quantity": "100",
        "unit_price": "500.00",
        "description": "أنابيب ري بالتنقيط 16 ملم"
    }, follow_redirects=True)
    
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    
    with app.app_context():
        item = InventoryItem.query.filter_by(sku="PIP-16").first()
        assert item is not None, "Stock item was not added!"
        assert item.quantity == 100
        assert item.unit_price == 500
        print("[OK] Stock item added successfully.")

    # 2. Create Invoice
    print("Creating a new invoice for client 'أحمد المحمد' with 20 units of 'أنابيب 16 ملم'...")
    res = client.post("/invoices/add", data={
        "client_name": "أحمد المحمد",
        "client_phone": "0987654321",
        "client_address": "دمشق - المزة",
        "discount": "0",
        "discount_type": "value",
        "tax_rate": "0",
        "status": "Paid",
        "description": ["أنابيب 16 ملم"],
        "quantity": ["20"],
        "unit_price": ["500.00"]
    }, follow_redirects=True)
    
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    
    with app.app_context():
        # Check stock deduction
        item = InventoryItem.query.filter_by(sku="PIP-16").first()
        print(f"Current stock quantity: {item.quantity}")
        assert item.quantity == 80, f"Expected stock quantity 80, but got {item.quantity}"
        print("[OK] Stock quantity successfully deducted to 80.")

        # Check invoice details
        invoice = Invoice.query.filter_by(client_name="أحمد المحمد").first()
        assert invoice is not None, "Invoice was not created!"
        assert invoice.total_amount == 10000, f"Expected total 10000, got {invoice.total_amount}"
        assert invoice.status == "Paid"
        print(f"[OK] Invoice created successfully with total: {invoice.total_amount} {invoice.invoice_number}")

    # 3. View Invoice Detail Page
    print("Testing invoice detail rendering...")
    res = client.get(f"/invoices/{invoice.id}")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "أحمد المحمد" in html
    assert "PIP-16" not in html # SKU is not displayed in details, description is
    assert "أنابيب 16 ملم" in html
    print("[OK] Invoice detail page rendered successfully!")

    # 4. View Dashboard
    print("Testing dashboard rendering...")
    res = client.get("/")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "لوحة التحكم" in html
    print("[OK] Dashboard page rendered successfully!")

print("\nALL TESTS PASSED SUCCESSFULLY! The application works exactly as expected!")
