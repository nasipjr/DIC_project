import json
from models import db, SystemSetting

DEFAULT_TREATMENT_PRICES = {
    "System Checkup": 50000,
    "Irrigation Design": 150000,
    "Piping Installation": 300000,
    "Pump Maintenance": 120000,
    "Drippers Setup": 80000,
    "Filter Cleaning": 30000,
    "System Optimization": 100000,
    "Urgent Leak Repair": 75000
}

DEFAULT_SETTINGS = {
    "clinic_name": "المركز التقني للري بالتنقيط",
    "clinic_phone": "+963 958 948 727",
    "clinic_email": "irrigation.tech.center@gmail.com",
    "clinic_address": "Damascus, Syria",
    "currency_symbol": "ل.س",
    "default_appointment_duration": "60",
    "working_hours_start": "08:00",
    "working_hours_end": "16:00",
    "working_days": "0,1,2,3,4,6",
    "treatment_prices": json.dumps(DEFAULT_TREATMENT_PRICES),
    "notification_enable_sms": "false",
    "notification_enable_whatsapp": "false",
    "notification_enable_email": "false",
    "twilio_account_sid": "",
    "twilio_auth_token": "",
    "twilio_phone_number": "",
    "twilio_whatsapp_number": "",
    "smtp_host": "smtp.gmail.com",
    "smtp_port": "587",
    "smtp_user": "",
    "smtp_password": "",
    "smtp_from_email": "",
    "tax_rate": "15",
    "clinic_vat_number": ""
}

from flask import g, has_app_context

def get_setting(key, default=None):
    if has_app_context():
        if not hasattr(g, "system_settings_cache"):
            g.system_settings_cache = {}
        if key in g.system_settings_cache:
            return g.system_settings_cache[key]

    val = None
    try:
        setting = SystemSetting.query.filter_by(key=key).first()
        if setting is not None:
            val = setting.value
    except Exception:
        pass

    if val is None:
        if default is not None:
            val = default
        else:
            val = DEFAULT_SETTINGS.get(key, None)

    if has_app_context():
        g.system_settings_cache[key] = val

    return val

def set_setting(key, value):
    try:
        setting = SystemSetting.query.filter_by(key=key).first()
        if setting:
            setting.value = str(value)
        else:
            setting = SystemSetting(key=key, value=str(value))
            db.session.add(setting)
        db.session.commit()

        if has_app_context():
            if not hasattr(g, "system_settings_cache"):
                g.system_settings_cache = {}
            g.system_settings_cache[key] = str(value)

        return True
    except Exception:
        db.session.rollback()
        return False

def get_currency_symbol():
    return get_setting("currency_symbol", "$")

def get_treatment_prices():
    val = get_setting("treatment_prices")
    if val:
        try:
            return json.loads(val)
        except Exception:
            pass
    return DEFAULT_TREATMENT_PRICES
