import sys
import os

# Add parent directory to path to import app and models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db, User
from utils.settings_helper import get_setting

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

    # 1. Access Settings Page (GET)
    print("Fetching settings page (GET)...")
    res = client.get("/settings")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    html = res.get_data(as_text=True)
    assert "settings" in html or "الإعدادات" in html
    print("[OK] Settings page rendered successfully.")

    # 2. Update Settings (POST)
    print("Updating settings: lang=en, theme=dark, currency_symbol=USD...")
    res = client.post("/settings", data={
        "lang": "en",
        "theme": "dark",
        "currency_symbol": "USD",
        "clinic_name": "Drip Irrigation Center Premium",
        "clinic_phone": "+123456789",
        "clinic_email": "premium.irrigation@example.com",
        "clinic_address": "USA"
    }, follow_redirects=True)
    
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    
    # 3. Verify Database Setting Updates
    with app.app_context():
        assert get_setting("currency_symbol") == "USD", f"Expected USD, got {get_setting('currency_symbol')}"
        assert get_setting("clinic_name") == "Drip Irrigation Center Premium"
        print("[OK] Database settings successfully updated.")

    # 4. Verify Theme and Language via Cookies on Dashboard Page
    print("Fetching dashboard page...")
    client.set_cookie("lang", "en")
    client.set_cookie("theme", "dark")
    
    res = client.get("/")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    html = res.get_data(as_text=True)
    
    # Check dynamic direction and dark theme attributes
    assert 'lang="en"' in html, "Expected lang='en' in html"
    assert 'dir="ltr"' in html, "Expected dir='ltr' in html"
    assert 'data-bs-theme="dark"' in html, "Expected dark theme in html tag"
    
    # Check translations work
    assert "Dashboard" in html, "Expected English translation 'Dashboard' in page"
    assert "Total Stock Items" in html, "Expected English translation 'Total Stock Items' in page"
    assert "Drip Irrigation Center Premium" in html, "Expected updated dynamic company name"
    
    print("[OK] Bilingual translation and theme toggle verified successfully on Dashboard!")

print("\nALL SETTINGS AND THEME TESTS PASSED SUCCESSFULLY!")
