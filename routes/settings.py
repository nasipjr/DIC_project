import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from utils.settings_helper import get_setting, set_setting, get_treatment_prices, DEFAULT_SETTINGS
from utils.auth_helper import role_required

settings_bp = Blueprint("settings", __name__)

@settings_bp.route("/settings", methods=["GET", "POST"])
@role_required("admin")
def settings_page():
    if request.method == "POST":
        current_app.logger.info("Updating system settings")
        try:
            # 1. Update general, calendar, and billing settings
            for key in ["clinic_name", "clinic_phone", "clinic_email", "clinic_address", 
                        "working_hours_start", "working_hours_end", "default_appointment_duration", 
                        "currency_symbol"]:
                val = request.form.get(key, "").strip()
                set_setting(key, val)

            # 1b. Update Twilio & SMTP Notification settings
            for key in ["twilio_account_sid", "twilio_auth_token", "twilio_phone_number", "twilio_whatsapp_number",
                        "smtp_host", "smtp_port", "smtp_user", "smtp_password", "smtp_from_email"]:
                val = request.form.get(key, "").strip()
                set_setting(key, val)

            sms_enabled = "true" if request.form.get("notification_enable_sms") else "false"
            whatsapp_enabled = "true" if request.form.get("notification_enable_whatsapp") else "false"
            email_enabled = "true" if request.form.get("notification_enable_email") else "false"
            set_setting("notification_enable_sms", sms_enabled)
            set_setting("notification_enable_whatsapp", whatsapp_enabled)
            set_setting("notification_enable_email", email_enabled)
            
            # Save working days checklist as a comma-separated string
            working_days_list = request.form.getlist("working_days")
            set_setting("working_days", ",".join(working_days_list))
            
            # 2. Update treatment prices (only if present in request to prevent clearing on partial form submissions)
            if "procedure_names[]" in request.form:
                names = request.form.getlist("procedure_names[]")
                prices = request.form.getlist("procedure_prices[]")
                
                treatment_dict = {}
                for name, price in zip(names, prices):
                    name = name.strip()
                    if name:
                        if len(name) > 200:
                            flash("Procedure name cannot exceed 200 characters.", "danger")
                            return redirect(url_for("settings.settings_page") + "#tab-treatments")
                        try:
                            # Convert price to number
                            price_clean = price.strip().replace(",", "")
                            price_val = float(price_clean) if '.' in price_clean else int(price_clean)
                            if price_val < 0:
                                price_val = 0
                        except ValueError:
                            price_val = 0
                        treatment_dict[name] = price_val
                
                set_setting("treatment_prices", json.dumps(treatment_dict))
            
            flash("Settings updated successfully!", "success")
            current_app.logger.info("Settings updated successfully")
        except Exception:
            current_app.logger.exception("Failed to update system settings")
            flash("Failed to update settings. Please try again.", "danger")
            
        active_tab = request.form.get("active_tab", "").strip()
        if active_tab and active_tab.startswith("#"):
            return redirect(url_for("settings.settings_page") + active_tab)
        return redirect(url_for("settings.settings_page"))

    # GET request: load values
    settings_data = {}
    for key in DEFAULT_SETTINGS.keys():
        settings_data[key] = get_setting(key)
        
    treatment_prices = get_treatment_prices()
    
    from models import User, NotificationLog
    users = User.query.all()
    notifications = NotificationLog.query.order_by(NotificationLog.sent_at.desc()).limit(100).all()

    # Read backups
    import os
    from utils.backup_helper import BACKUP_DIR
    from datetime import datetime
    backups_list = []
    if os.path.exists(BACKUP_DIR):
        for f in os.listdir(BACKUP_DIR):
            p = os.path.join(BACKUP_DIR, f)
            if os.path.isfile(p) and f.startswith('backup_') and (f.endswith('.sql') or f.endswith('.db')):
                stats = os.stat(p)
                size_kb = round(stats.st_size / 1024, 2)
                mtime = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                backups_list.append({
                    'filename': f,
                    'mtime': mtime,
                    'size': f"{size_kb} KB"
                })
        # Sort backups by date descending (newest first)
        backups_list.sort(key=lambda x: x['mtime'], reverse=True)
    
    return render_template(
        "settings/settings.html",
        settings=settings_data,
        treatment_prices=treatment_prices,
        users=users,
        backups=backups_list,
        notifications=notifications
    )


@settings_bp.route("/settings/users/add", methods=["POST"])
@role_required("admin")
def add_user():
    from models import db, User
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    role = request.form.get("role", "receptionist").strip()
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()

    if not username or not password:
        flash("Username and Password are required.", "danger")
        return redirect(url_for("settings.settings_page") + "#tab-users")

    if len(username) > 80:
        flash("Username cannot exceed 80 characters.", "danger")
        return redirect(url_for("settings.settings_page") + "#tab-users")

    if len(password) < 6:
        flash("Password must be at least 6 characters long.", "danger")
        return redirect(url_for("settings.settings_page") + "#tab-users")

    if role not in {"admin", "doctor", "receptionist"}:
        flash("Invalid user role specified.", "danger")
        return redirect(url_for("settings.settings_page") + "#tab-users")

    if len(first_name) > 100 or len(last_name) > 100:
        flash("First name and Last name cannot exceed 100 characters.", "danger")
        return redirect(url_for("settings.settings_page") + "#tab-users")

    existing = User.query.filter_by(username=username).first()
    if existing:
        flash("Username already exists.", "danger")
        return redirect(url_for("settings.settings_page"))

    try:
        new_user = User(
            username=username,
            role=role,
            first_name=first_name,
            last_name=last_name
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash(f"User account '{username}' created successfully!", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to add user: {e}")
        flash("Failed to create user account.", "danger")

    return redirect(url_for("settings.settings_page") + "#tab-users")


@settings_bp.route("/settings/users/<int:user_id>/delete", methods=["POST"])
@role_required("admin")
def delete_user(user_id):
    from models import db, User
    from flask import session
    
    # Prevent deleting oneself
    if session.get("user_id") == user_id:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("settings.settings_page") + "#tab-users")

    user = User.query.get(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("settings.settings_page") + "#tab-users")

    try:
        db.session.delete(user)
        db.session.commit()
        flash(f"User account '{user.username}' deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to delete user: {e}")
        flash("Failed to delete user account.", "danger")

    return redirect(url_for("settings.settings_page") + "#tab-users")


@settings_bp.route("/settings/users/<int:user_id>/edit", methods=["POST"])
@role_required("admin")
def edit_user(user_id):
    from models import db, User
    from flask import session

    user = User.query.get(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("settings.settings_page") + "#tab-users")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    role = request.form.get("role", "").strip()
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()

    if not username:
        flash("Username is required.", "danger")
        return redirect(url_for("settings.settings_page") + "#tab-users")

    if len(username) > 80:
        flash("Username cannot exceed 80 characters.", "danger")
        return redirect(url_for("settings.settings_page") + "#tab-users")

    if password and len(password) < 6:
        flash("Password must be at least 6 characters long.", "danger")
        return redirect(url_for("settings.settings_page") + "#tab-users")

    if role and role not in {"admin", "doctor", "receptionist"}:
        flash("Invalid user role specified.", "danger")
        return redirect(url_for("settings.settings_page") + "#tab-users")

    if len(first_name) > 100 or len(last_name) > 100:
        flash("First name and Last name cannot exceed 100 characters.", "danger")
        return redirect(url_for("settings.settings_page") + "#tab-users")

    # Check if username is taken by another user
    existing = User.query.filter(User.username == username, User.id != user_id).first()
    if existing:
        flash("Username already taken by another user.", "danger")
        return redirect(url_for("settings.settings_page") + "#tab-users")

    try:
        user.username = username
        user.first_name = first_name
        user.last_name = last_name

        if role:
            user.role = role

        # Only update password if provided
        if password:
            user.set_password(password)

        db.session.commit()
        flash(f"User account '{username}' updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to update user: {e}")
        flash("Failed to update user account.", "danger")

    return redirect(url_for("settings.settings_page") + "#tab-users")


@settings_bp.route("/settings/backups/create", methods=["POST"])
@role_required("admin")
def create_backup():
    try:
        from utils.backup_helper import run_database_backup
        filename = run_database_backup()
        flash(f"Backup created successfully: {filename}", "success")
    except Exception as e:
        current_app.logger.exception("Failed to create database backup")
        flash(f"Failed to create database backup: {e}", "danger")
    return redirect(url_for("settings.settings_page") + "#tab-backups")


@settings_bp.route("/settings/backups/<filename>/download")
@role_required("admin")
def download_backup(filename):
    import os
    from flask import send_from_directory, abort
    from utils.backup_helper import BACKUP_DIR
    
    # Secure filename check to prevent directory traversal
    if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
        abort(400, "Invalid backup filename.")
        
    backup_path = os.path.join(BACKUP_DIR, filename)
    if os.path.exists(backup_path) and os.path.isfile(backup_path):
        return send_from_directory(BACKUP_DIR, filename, as_attachment=True)
    else:
        flash("Backup file not found.", "danger")
        return redirect(url_for("settings.settings_page") + "#tab-backups")


@settings_bp.route("/settings/backups/<filename>/delete", methods=["POST"])
@role_required("admin")
def delete_backup(filename):
    import os
    from flask import abort
    from utils.backup_helper import BACKUP_DIR
    
    # Secure filename check to prevent directory traversal
    if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
        abort(400, "Invalid backup filename.")
        
    backup_path = os.path.join(BACKUP_DIR, filename)
    if os.path.exists(backup_path) and os.path.isfile(backup_path):
        try:
            os.remove(backup_path)
            flash("Backup file deleted successfully.", "success")
        except Exception as e:
            current_app.logger.error(f"Failed to delete backup file: {e}")
            flash("Failed to delete backup file.", "danger")
    else:
        flash("Backup file not found.", "danger")
        
    return redirect(url_for("settings.settings_page") + "#tab-backups")
