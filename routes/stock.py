from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash
from models import db, InventoryItem
from utils.auth_helper import role_required
from decimal import Decimal

stock_bp = Blueprint("stock", __name__)

@stock_bp.route("/stock")
@role_required("admin")
def list_stock():
    current_app.logger.info("Stock inventory list opened")
    search_query = request.args.get("search", "").strip()
    
    query = InventoryItem.query
    if search_query:
        query = query.filter(
            (InventoryItem.name.ilike(f"%{search_query}%")) |
            (InventoryItem.sku.ilike(f"%{search_query}%"))
        )
    
    items = query.order_by(InventoryItem.name.asc()).all()
    
    # Calculate simple stats
    total_items = len(items)
    low_stock_count = sum(1 for item in items if item.quantity < 10)
    total_value = sum(Decimal(str(item.unit_price or 0)) * (item.quantity or 0) for item in items)
    
    return render_template(
        "stock/list.html",
        items=items,
        search_query=search_query,
        total_items=total_items,
        low_stock_count=low_stock_count,
        total_value=total_value
    )

@stock_bp.route("/stock/add", methods=["GET", "POST"])
@role_required("admin")
def add_item():
    import json
    from utils.settings_helper import get_setting
    
    # Load dynamic companies list
    companies_str = get_setting("companies")
    companies = []
    if companies_str:
        try:
            companies = json.loads(companies_str)
        except Exception:
            pass
    if not companies:
        companies = ["Rain Bird", "Hunter", "Netafim", "Toro"]

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        sku = request.form.get("sku", "").strip() or None
        quantity_raw = request.form.get("quantity", "0").strip()
        unit_price_raw = request.form.get("unit_price", "0").strip()
        company = request.form.get("company", "").strip() or None
        description = request.form.get("description", "").strip()
        
        if not name:
            flash("Item name is required.", "danger")
            return render_template("stock/add_edit.html", mode="add", companies=companies)
            
        try:
            quantity = int(quantity_raw)
            unit_price = Decimal(unit_price_raw)
        except ValueError:
            flash("Invalid quantity or unit price.", "danger")
            return render_template("stock/add_edit.html", mode="add", companies=companies)
            
        # Check SKU uniqueness
        if sku:
            existing = InventoryItem.query.filter_by(sku=sku).first()
            if existing:
                flash("SKU must be unique. An item with this SKU already exists.", "danger")
                return render_template("stock/add_edit.html", mode="add", companies=companies)
                
        try:
            new_item = InventoryItem(
                name=name,
                sku=sku,
                quantity=quantity,
                unit_price=unit_price,
                company=company,
                description=description
            )
            db.session.add(new_item)
            db.session.commit()
            flash(f"Item '{name}' added successfully to stock.", "success")
            return redirect(url_for("stock.list_stock"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(f"Failed to add inventory item: {e}")
            flash("Failed to add item due to a database error.", "danger")
            
    return render_template("stock/add_edit.html", mode="add", companies=companies)

@stock_bp.route("/stock/edit/<int:item_id>", methods=["GET", "POST"])
@role_required("admin")
def edit_item(item_id):
    import json
    from utils.settings_helper import get_setting
    item = InventoryItem.query.get_or_404(item_id)
    
    # Load dynamic companies list
    companies_str = get_setting("companies")
    companies = []
    if companies_str:
        try:
            companies = json.loads(companies_str)
        except Exception:
            pass
    if not companies:
        companies = ["Rain Bird", "Hunter", "Netafim", "Toro"]
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        sku = request.form.get("sku", "").strip() or None
        quantity_raw = request.form.get("quantity", "0").strip()
        unit_price_raw = request.form.get("unit_price", "0").strip()
        company = request.form.get("company", "").strip() or None
        description = request.form.get("description", "").strip()
        
        if not name:
            flash("Item name is required.", "danger")
            return render_template("stock/add_edit.html", item=item, mode="edit", companies=companies)
            
        try:
            quantity = int(quantity_raw)
            unit_price = Decimal(unit_price_raw)
        except ValueError:
            flash("Invalid quantity or unit price.", "danger")
            return render_template("stock/add_edit.html", item=item, mode="edit", companies=companies)
            
        # Check SKU uniqueness
        if sku and sku != item.sku:
            existing = InventoryItem.query.filter_by(sku=sku).first()
            if existing:
                flash("SKU must be unique. An item with this SKU already exists.", "danger")
                return render_template("stock/add_edit.html", item=item, mode="edit", companies=companies)
                
        try:
            item.name = name
            item.sku = sku
            item.quantity = quantity
            item.unit_price = unit_price
            item.company = company
            item.description = description
            db.session.commit()
            flash(f"Item '{name}' updated successfully.", "success")
            return redirect(url_for("stock.list_stock"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(f"Failed to update inventory item {item_id}: {e}")
            flash("Failed to update item due to a database error.", "danger")
            
    return render_template("stock/add_edit.html", item=item, mode="edit", companies=companies)

@stock_bp.route("/stock/delete/<int:item_id>", methods=["POST"])
@role_required("admin")
def delete_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    name = item.name
    try:
        db.session.delete(item)
        db.session.commit()
        flash(f"Item '{name}' deleted from inventory.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Failed to delete inventory item {item_id}: {e}")
        flash("Failed to delete item due to a database error.", "danger")
        
    return redirect(url_for("stock.list_stock"))

@stock_bp.route("/stock/adjust/<int:item_id>", methods=["POST"])
@role_required("admin")
def adjust_quantity(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    adjustment_raw = request.form.get("adjustment", "0").strip()
    
    try:
        adjustment = int(adjustment_raw)
        if item.quantity + adjustment < 0:
            flash("Stock quantity cannot be less than 0.", "danger")
        else:
            item.quantity += adjustment
            db.session.commit()
            flash(f"Stock for '{item.name}' adjusted by {adjustment:+} units.", "success")
    except ValueError:
        flash("Invalid adjustment value.", "danger")
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Failed to adjust stock for item {item_id}: {e}")
        flash("Failed to adjust stock due to database error.", "danger")
        
    return redirect(url_for("stock.list_stock"))
