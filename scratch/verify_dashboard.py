import sys
import os

sys.path.append(os.path.abspath(r"c:\Users\Windows.11\Desktop\Dental Clinic MS Flask"))

from app import app
from models import db, User

client = app.test_client()

print("Simulating admin login session...")
with client:
    with client.session_transaction() as sess:
        with app.app_context():
            admin_user = User.query.filter_by(role="admin").first()
            sess["user_id"] = admin_user.id
            sess["role"] = admin_user.role

    print("Fetching home page...")
    res = client.get("/")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    html = res.get_data(as_text=True)
    
    # Assert dynamic hours badge works
    assert "Working Hours" in html
    # Assert canvas for dynamic chart exists
    assert "dashboardOverviewChart" in html
    # Assert Chart.js is loaded
    assert "chart.js" in html

    print("SUCCESS: Dashboard rendered successfully with Chart.js and dynamic hours badge!")
