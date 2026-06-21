from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from models import db, User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard.home"))

    lang = request.cookies.get('lang', 'en')

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            err_msg = {
                "ar": "يرجى إدخال اسم المستخدم وكلمة المرور.",
                "en": "Please enter both username and password."
            }.get(lang, "Please enter both username and password.")
            flash(err_msg, "danger")
            return render_template("auth/login.html")

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session["user_id"] = user.id
            session["role"] = user.role
            name_to_use = user.first_name or user.username
            
            welcome_msg = {
                "ar": f"مرحباً بك مجدداً، {name_to_use}!",
                "en": f"Welcome back, {name_to_use}!"
            }.get(lang, f"Welcome back, {name_to_use}!")
            
            session.permanent = True
            flash(welcome_msg, "success")
            return redirect(url_for("dashboard.home"))
        else:
            invalid_msg = {
                "ar": "اسم المستخدم أو كلمة المرور غير صالحة.",
                "en": "Invalid username or password."
            }.get(lang, "Invalid username or password.")
            flash(invalid_msg, "danger")
            return render_template("auth/login.html")

    return render_template("auth/login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("auth.login"))
