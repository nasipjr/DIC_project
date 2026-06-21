import os
import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, send_file, g
from utils.auth_helper import role_required
from utils.settings_helper import get_setting, set_setting, get_treatment_prices
from models import db

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/settings", methods=["GET", "POST"])
@role_required("admin")
def settings():
    active_tab = request.args.get("tab", "profile")

    if request.method == "POST":
        lang = request.form.get("lang", "ar").strip()
        theme = request.form.get("theme", "light").strip()
        active_tab = request.form.get("active_tab", "profile").strip()

        # Save Text settings
        set_setting("currency_symbol", request.form.get("currency_symbol", "$").strip())
        
        clinic_name = request.form.get("clinic_name", "").strip()
        if clinic_name:
            set_setting("clinic_name", clinic_name)
            
        clinic_phone = request.form.get("clinic_phone", "").strip()
        if clinic_phone:
            set_setting("clinic_phone", clinic_phone)
            
        clinic_email = request.form.get("clinic_email", "").strip()
        if clinic_email:
            set_setting("clinic_email", clinic_email)
            
        clinic_address = request.form.get("clinic_address", "").strip()
        if clinic_address:
            set_setting("clinic_address", clinic_address)

        set_setting("clinic_description", request.form.get("clinic_description", "").strip())
        set_setting("social_facebook", request.form.get("social_facebook", "").strip())
        set_setting("social_instagram", request.form.get("social_instagram", "").strip())
        set_setting("social_linkedin", request.form.get("social_linkedin", "").strip())
        set_setting("social_whatsapp", request.form.get("social_whatsapp", "").strip())
        # Compile working days from checkboxes
        selected_days = request.form.getlist("working_days")
        working_days_list = [d for d in selected_days if d.strip() in ['0','1','2','3','4','5','6']]
        working_days_list.sort()
        working_days_str = ",".join(working_days_list)
        set_setting("working_days", working_days_str)
        
        # Save working hours start/end
        working_hours_start = request.form.get("working_hours_start", "08:00").strip()
        working_hours_end = request.form.get("working_hours_end", "16:00").strip()
        set_setting("working_hours_start", working_hours_start)
        set_setting("working_hours_end", working_hours_end)
        
        # Generate user-friendly text descriptions for footer/display
        days_ar = {'0': 'الأحد', '1': 'الاثنين', '2': 'الثلاثاء', '3': 'الأربعاء', '4': 'الخميس', '5': 'الجمعة', '6': 'السبت'}
        days_en = {'0': 'Sunday', '1': 'Monday', '2': 'Tuesday', '3': 'Wednesday', '4': 'Thursday', '5': 'Friday', '6': 'Saturday'}
        
        def format_time(t_str):
            try:
                dt = datetime.strptime(t_str.strip(), "%H:%M")
                if lang == 'ar':
                    period = "ص" if dt.hour < 12 else "م"
                    hour = dt.hour if dt.hour <= 12 else dt.hour - 12
                    if hour == 0:
                        hour = 12
                    return f"{hour}:{dt.minute:02d} {period}"
                else:
                    return dt.strftime("%I:%M %p")
            except Exception:
                return t_str
                
        formatted_start = format_time(working_hours_start)
        formatted_end = format_time(working_hours_end)
        time_range = f"{formatted_start} - {formatted_end}"
        
        checked_days = [int(d) for d in working_days_list]
        off_days = [d for d in [0,1,2,3,4,5,6] if d not in checked_days]
        
        if lang == 'ar':
            if not checked_days:
                weekdays_text = "مغلق تماماً"
                weekend_text = "طيلة أيام الأسبوع"
            elif len(checked_days) == 7:
                weekdays_text = f"طيلة أيام الأسبوع: {time_range}"
                weekend_text = "لا يوجد عطلة"
            else:
                standard_working = {0, 1, 2, 3, 4, 6}
                if set(checked_days) == standard_working:
                    weekdays_text = f"السبت - الخميس: {time_range}"
                    weekend_text = "الجمعة: مغلق"
                else:
                    checked_names = [days_ar[str(d)] for d in checked_days]
                    weekdays_text = f"أيام العمل ({', '.join(checked_names)}): {time_range}"
                    off_names = [days_ar[str(d)] for d in off_days]
                    weekend_text = f"العطلة: {', '.join(off_names)}"
        else:
            if not checked_days:
                weekdays_text = "Closed all week"
                weekend_text = "Every day"
            elif len(checked_days) == 7:
                weekdays_text = f"Every day: {time_range}"
                weekend_text = "No holidays"
            else:
                standard_working = {0, 1, 2, 3, 4, 6}
                if set(checked_days) == standard_working:
                    weekdays_text = f"Saturday - Thursday: {time_range}"
                    weekend_text = "Friday: Closed"
                else:
                    checked_names = [days_en[str(d)] for d in checked_days]
                    weekdays_text = f"Working Days ({', '.join(checked_names)}): {time_range}"
                    off_names = [days_en[str(d)] for d in off_days]
                    weekend_text = f"Holidays: {', '.join(off_names)}"
                    
        set_setting("operating_hours_weekdays", weekdays_text)
        set_setting("operating_hours_weekend", weekend_text)

        # Billing and Finance Settings
        set_setting("tax_rate", request.form.get("tax_rate", "0").strip())
        set_setting("clinic_vat_number", request.form.get("clinic_vat_number", "").strip())

        # Notification Settings
        set_setting("notification_enable_sms", request.form.get("notification_enable_sms") or "false")
        set_setting("notification_enable_whatsapp", request.form.get("notification_enable_whatsapp") or "false")
        set_setting("notification_enable_email", request.form.get("notification_enable_email") or "false")
        
        set_setting("twilio_account_sid", request.form.get("twilio_account_sid", "").strip())
        set_setting("twilio_auth_token", request.form.get("twilio_auth_token", "").strip())
        set_setting("twilio_phone_number", request.form.get("twilio_phone_number", "").strip())
        set_setting("twilio_whatsapp_number", request.form.get("twilio_whatsapp_number", "").strip())
        
        set_setting("smtp_host", request.form.get("smtp_host", "").strip())
        set_setting("smtp_port", request.form.get("smtp_port", "").strip())
        set_setting("smtp_user", request.form.get("smtp_user", "").strip())
        set_setting("smtp_password", request.form.get("smtp_password", "").strip())
        set_setting("smtp_from_email", request.form.get("smtp_from_email", "").strip())

        # Pricing settings
        current_prices = get_treatment_prices()
        updated_prices = {}
        for key in current_prices.keys():
            form_val = request.form.get(f"price_{key}", "").strip()
            if form_val:
                try:
                    updated_prices[key] = int(form_val)
                except ValueError:
                    updated_prices[key] = current_prices[key]
            else:
                updated_prices[key] = current_prices[key]
        set_setting("treatment_prices", json.dumps(updated_prices))

        # Save Companies settings
        companies_raw_list = request.form.getlist("companies")
        companies_list = []
        for name in companies_raw_list:
            name_cleaned = name.strip()
            if name_cleaned:
                companies_list.append(name_cleaned)
        set_setting("companies", json.dumps(companies_list))

        # Admin user accounts update
        if g.current_user:
            admin_first_name = request.form.get("admin_first_name", "").strip()
            admin_last_name = request.form.get("admin_last_name", "").strip()
            admin_password = request.form.get("admin_password", "").strip()
            
            if admin_first_name:
                g.current_user.first_name = admin_first_name
            if admin_last_name:
                g.current_user.last_name = admin_last_name
            if admin_password:
                g.current_user.set_password(admin_password)
            db.session.commit()

        # Set cookies for language and theme
        response = make_response(redirect(url_for("settings.settings", tab=active_tab)))
        response.set_cookie("lang", lang, max_age=30*24*60*60)
        response.set_cookie("theme", theme, max_age=30*24*60*60)

        # Flash success message
        success_msg = {
            "ar": "تم حفظ الإعدادات بنجاح.",
            "en": "Settings saved successfully."
        }.get(lang, "Settings saved.")
        
        flash(success_msg, "success")
        return response

    # GET request
    currency_symbol = get_setting("currency_symbol", "$")
    clinic_name = get_setting("clinic_name", "المركز التقني للري بالتنقيط")
    clinic_phone = get_setting("clinic_phone", "+963 958 948 727")
    clinic_email = get_setting("clinic_email", "irrigation.tech.center@gmail.com")
    clinic_address = get_setting("clinic_address", "Damascus, Syria")
    clinic_description = get_setting("clinic_description", "")
    social_facebook = get_setting("social_facebook", "")
    social_instagram = get_setting("social_instagram", "")
    social_linkedin = get_setting("social_linkedin", "")
    social_whatsapp = get_setting("social_whatsapp", "")
    operating_hours_weekdays = get_setting("operating_hours_weekdays", "")
    operating_hours_weekend = get_setting("operating_hours_weekend", "")
    working_days = get_setting("working_days", "0,1,2,3,4,6")
    working_hours_start = get_setting("working_hours_start", "08:00")
    working_hours_end = get_setting("working_hours_end", "16:00")
    
    tax_rate = get_setting("tax_rate", "0")
    clinic_vat_number = get_setting("clinic_vat_number", "")
    
    notification_enable_sms = get_setting("notification_enable_sms", "false")
    notification_enable_whatsapp = get_setting("notification_enable_whatsapp", "false")
    notification_enable_email = get_setting("notification_enable_email", "false")
    
    twilio_account_sid = get_setting("twilio_account_sid", "")
    twilio_auth_token = get_setting("twilio_auth_token", "")
    twilio_phone_number = get_setting("twilio_phone_number", "")
    twilio_whatsapp_number = get_setting("twilio_whatsapp_number", "")
    
    smtp_host = get_setting("smtp_host", "")
    smtp_port = get_setting("smtp_port", "")
    smtp_user = get_setting("smtp_user", "")
    smtp_password = get_setting("smtp_password", "")
    smtp_from_email = get_setting("smtp_from_email", "")

    # Get recent backups list
    from utils.backup_helper import BACKUP_DIR
    backups = []
    if os.path.exists(BACKUP_DIR):
        for f in os.listdir(BACKUP_DIR):
            p = os.path.join(BACKUP_DIR, f)
            if os.path.isfile(p) and (f.endswith('.sql') or f.endswith('.db')):
                backups.append({
                    "filename": f,
                    "size_kb": round(os.path.getsize(p) / 1024, 2),
                    "created_at": datetime.fromtimestamp(os.path.getmtime(p)).strftime('%Y-%m-%d %H:%M:%S')
                })
        backups.sort(key=lambda x: x['created_at'], reverse=True)

    treatment_prices = get_treatment_prices()

    # Get companies list
    companies_str = get_setting("companies")
    companies_list = []
    if companies_str:
        try:
            companies_list = json.loads(companies_str)
        except Exception:
            pass
    if not companies_list:
        companies_list = ["Rain Bird", "Hunter", "Netafim", "Toro"]
    companies_val = "\n".join(companies_list)

    return render_template(
        "settings/index.html",
        companies_val=companies_val,
        companies_list=companies_list,
        active_tab=active_tab,
        currency_symbol_val=currency_symbol,
        clinic_name_val=clinic_name,
        clinic_phone_val=clinic_phone,
        clinic_email_val=clinic_email,
        clinic_address_val=clinic_address,
        clinic_description_val=clinic_description,
        social_facebook_val=social_facebook,
        social_instagram_val=social_instagram,
        social_linkedin_val=social_linkedin,
        social_whatsapp_val=social_whatsapp,
        operating_hours_weekdays_val=operating_hours_weekdays,
        operating_hours_weekend_val=operating_hours_weekend,
        working_days_val=working_days,
        working_hours_start_val=working_hours_start,
        working_hours_end_val=working_hours_end,
        tax_rate_val=tax_rate,
        clinic_vat_number_val=clinic_vat_number,
        notification_enable_sms_val=notification_enable_sms,
        notification_enable_whatsapp_val=notification_enable_whatsapp,
        notification_enable_email_val=notification_enable_email,
        twilio_account_sid_val=twilio_account_sid,
        twilio_auth_token_val=twilio_auth_token,
        twilio_phone_number_val=twilio_phone_number,
        twilio_whatsapp_number_val=twilio_whatsapp_number,
        smtp_host_val=smtp_host,
        smtp_port_val=smtp_port,
        smtp_user_val=smtp_user,
        smtp_password_val=smtp_password,
        smtp_from_email_val=smtp_from_email,
        backups=backups,
        treatment_prices=treatment_prices
    )


@settings_bp.route("/settings/backup/run", methods=["POST"])
@role_required("admin")
def run_backup():
    try:
        from utils.backup_helper import run_database_backup
        filename = run_database_backup()
        flash(f"تم إنشاء نسخة احتياطية جديدة بنجاح: {filename}", "success")
    except Exception as e:
        flash(f"فشل إنشاء النسخة الاحتياطية: {e}", "danger")
    return redirect(url_for("settings.settings", tab="backups"))


@settings_bp.route("/settings/backup/delete/<filename>", methods=["POST"])
@role_required("admin")
def delete_backup(filename):
    try:
        from utils.backup_helper import BACKUP_DIR
        filepath = os.path.join(BACKUP_DIR, filename)
        if os.path.exists(filepath) and os.path.commonpath([BACKUP_DIR, filepath]) == BACKUP_DIR:
            os.remove(filepath)
            flash("تم حذف ملف النسخة الاحتياطية بنجاح.", "success")
        else:
            flash("الملف غير موجود أو المسار غير صالح.", "danger")
    except Exception as e:
        flash(f"خطأ أثناء حذف الملف: {e}", "danger")
    return redirect(url_for("settings.settings", tab="backups"))


@settings_bp.route("/settings/backup/download/<filename>")
@role_required("admin")
def download_backup(filename):
    try:
        from utils.backup_helper import BACKUP_DIR
        filepath = os.path.join(BACKUP_DIR, filename)
        if os.path.exists(filepath) and os.path.commonpath([BACKUP_DIR, filepath]) == BACKUP_DIR:
            return send_file(filepath, as_attachment=True)
        else:
            flash("الملف غير موجود.", "danger")
    except Exception:
        flash("فشل تحميل الملف.", "danger")
    return redirect(url_for("settings.settings", tab="backups"))

