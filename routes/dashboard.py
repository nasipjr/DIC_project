from flask import Blueprint, current_app, render_template
from models import db, InventoryItem, Invoice
from utils.auth_helper import role_required
from sqlalchemy import func

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@role_required("admin")
def home():
    current_app.logger.info("Home page opened")

    try:
        from models import Client, Payment
        total_clients = Client.query.count()
        total_stock_items = InventoryItem.query.count()
        low_stock_count = InventoryItem.query.filter(InventoryItem.quantity < 10).count()
        total_invoices = Invoice.query.count()
        paid_invoices = Invoice.query.filter_by(status="Paid").count()
        unpaid_invoices = Invoice.query.filter_by(status="Unpaid").count()

        total_revenue = db.session.query(func.sum(Invoice.total_amount)).scalar() or 0.0
        paid_revenue = db.session.query(func.sum(Invoice.total_amount)).filter_by(status="Paid").scalar() or 0.0
        unpaid_revenue = db.session.query(func.sum(Invoice.total_amount)).filter_by(status="Unpaid").scalar() or 0.0

        total_revenue = float(total_revenue)
        paid_revenue = float(paid_revenue)
        unpaid_revenue = float(unpaid_revenue)

        total_payments = db.session.query(func.sum(Payment.amount)).scalar() or 0.0
        total_payments = float(total_payments)

        invoices = Invoice.query.all()
        total_debt = float(sum(inv.outstanding_amount for inv in invoices))

        clients = Client.query.all()
        total_credit = float(sum(c.credit for c in clients))

        recent_invoices = Invoice.query.order_by(Invoice.issue_date.desc()).limit(5).all()
        low_stock_items = InventoryItem.query.filter(InventoryItem.quantity < 10).order_by(InventoryItem.quantity.asc()).limit(5).all()

        return render_template(
            "dashboard/index.html",
            total_clients=total_clients,
            total_stock_items=total_stock_items,
            low_stock_count=low_stock_count,
            total_invoices=total_invoices,
            paid_invoices=paid_invoices,
            unpaid_invoices=unpaid_invoices,
            total_revenue=total_revenue,
            paid_revenue=paid_revenue,
            unpaid_revenue=unpaid_revenue,
            total_payments=total_payments,
            total_debt=total_debt,
            total_credit=total_credit,
            recent_invoices=recent_invoices,
            low_stock_items=low_stock_items
        )

    except Exception:
        current_app.logger.exception("Error while loading home page")
        return "Error Loading MainPage", 500


@dashboard_bp.route("/calendar")
@role_required("admin")
def view_calendar():
    from flask import request
    from datetime import datetime, date
    import calendar as pycalendar
    from sqlalchemy import func
    from models import Invoice, Payment
    
    today = date.today()
    try:
        year = int(request.args.get("year", today.year))
        month = int(request.args.get("month", today.month))
    except ValueError:
        year = today.year
        month = today.month

    # Get working days settings
    from utils.settings_helper import get_setting
    working_days_setting = get_setting("working_days", "0,1,2,3,4,6")
    working_days = [int(d) for d in working_days_setting.split(",") if d.strip().isdigit()]

    # Query invoices in this month
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    # Fetch all invoices created in this month
    invoices = Invoice.query.filter(Invoice.issue_date >= start_date, Invoice.issue_date < end_date).all()

    # Fetch all payments received in this month
    payments = Payment.query.filter(Payment.payment_date >= start_date, Payment.payment_date < end_date).all()

    # Aggregate by day
    num_days = pycalendar.monthrange(year, month)[1]
    days_data = {
        d: {
            "invoices_count": 0,
            "invoices_amount": 0.0,
            "payments_amount": 0.0,
            "items_sold_count": 0,
            "invoices": [],
            "payments": []
        }
        for d in range(1, num_days + 1)
    }

    for inv in invoices:
        d = inv.issue_date.day
        if d in days_data:
            days_data[d]["invoices_count"] += 1
            days_data[d]["invoices_amount"] += float(inv.total_amount)
            # count items sold in this invoice
            days_data[d]["items_sold_count"] += sum(item.quantity for item in inv.items)
            
            client_obj = inv.client
            client_id = client_obj.id if client_obj else None
            
            days_data[d]["invoices"].append({
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "client_name": inv.client_name,
                "client_id": client_id,
                "total_amount": float(inv.total_amount),
                "outstanding_amount": float(inv.outstanding_amount),
                "status": inv.status
            })

    for p in payments:
        d = p.payment_date.day
        if d in days_data:
            days_data[d]["payments_amount"] += float(p.amount)
            client_name = p.client.name if p.client else "N/A"
            days_data[d]["payments"].append({
                "id": p.id,
                "payment_number": p.payment_number,
                "client_id": p.client_id,
                "client_name": client_name,
                "amount": float(p.amount),
                "notes": p.notes or ""
            })

    # Let's calculate monthly totals
    total_sales = sum(d["invoices_amount"] for d in days_data.values())
    total_paid = sum(d["payments_amount"] for d in days_data.values())
    total_invoices_count = sum(d["invoices_count"] for d in days_data.values())

    # Build weekly analytics
    chart_labels = [f"{year}-{month:02d}-{d:02d}" for d in range(1, num_days + 1)]
    chart_sales = [days_data[d]["invoices_amount"] for d in range(1, num_days + 1)]
    chart_payments = [days_data[d]["payments_amount"] for d in range(1, num_days + 1)]

    # Calendar grid generation (Sunday-start)
    py_first_weekday = pycalendar.monthrange(year, month)[0] # 0 = Monday, 6 = Sunday
    first_day_index = (py_first_weekday + 1) % 7 # maps 6 (Sunday) -> 0, 0 -> 1 ...
    
    grid = []
    current_row = [None] * first_day_index
    for d in range(1, num_days + 1):
        current_row.append(d)
        if len(current_row) == 7:
            grid.append(current_row)
            current_row = []
    if current_row:
        current_row += [None] * (7 - len(current_row))
        grid.append(current_row)

    # Arabic month name helper
    arabic_months = {
        1: "كانون الثاني (يناير)",
        2: "شباط (فبراير)",
        3: "آذار (مارس)",
        4: "نيسان (أبريل)",
        5: "أيار (مايو)",
        6: "حزيران (يونيو)",
        7: "تموز (يوليو)",
        8: "آب (أغسطس)",
        9: "أيلول (سبتمبر)",
        10: "تشرين الأول (أكتوبر)",
        11: "تشرين الثاني (نوفمبر)",
        12: "كانون الأول (ديسمبر)"
    }
    month_name = arabic_months.get(month, "")

    # Calculate weekly summaries
    weekly_summaries = []
    for idx, row in enumerate(grid):
        week_sales = 0.0
        week_payments = 0.0
        week_days = []
        for day in row:
            if day:
                week_sales += days_data[day]["invoices_amount"]
                week_payments += days_data[day]["payments_amount"]
                week_days.append(day)
        if week_days:
            start_day = week_days[0]
            end_day = week_days[-1]
            weekly_summaries.append({
                "label": f"الأسبوع {idx + 1} ({start_day} - {end_day})",
                "sales": week_sales,
                "payments": week_payments
            })

    return render_template(
        "dashboard/calendar.html",
        grid=grid,
        year=year,
        month=month,
        month_name=month_name,
        days_data=days_data,
        working_days=working_days,
        total_sales=total_sales,
        total_paid=total_paid,
        today=today,
        total_invoices_count=total_invoices_count,
        chart_labels=chart_labels,
        chart_sales=chart_sales,
        chart_payments=chart_payments,
        weekly_summaries=weekly_summaries,
        prev_month=12 if month == 1 else month - 1,
        prev_year=year - 1 if month == 1 else year,
        next_month=1 if month == 12 else month + 1,
        next_year=year + 1 if month == 12 else year
    )