from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash

from models import db, Patient, Appointment, Treatment, Payment, Invoice, PatientFile
from utils.validators import parse_patient_data
from utils.auth_helper import role_required


patients_bp = Blueprint("patients", __name__)


def get_patients_context():
    search_query = request.args.get("search", "")
    sort_by = request.args.get("sort", "id")
    order = request.args.get("order", "desc")
    page = request.args.get("page", 1, type=int)
    per_page = 10

    query = Patient.query

    if search_query:
        query = query.filter(
            (Patient.first_name.ilike(f"%{search_query}%")) |
            (Patient.last_name.ilike(f"%{search_query}%")) |
            (Patient.phone.ilike(f"%{search_query}%")) |
            (Patient.email.ilike(f"%{search_query}%")) |
            (Patient.city.ilike(f"%{search_query}%"))
        )

    sort_columns = {
        "id": Patient.id,
        "first_name": Patient.first_name,
        "last_name": Patient.last_name,
        "phone": Patient.phone,
        "email": Patient.email,
        "city": Patient.city,
        "date_of_birth": Patient.date_of_birth,
    }

    sort_column = sort_columns.get(sort_by, Patient.id)

    if order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )

    return {
        "patients": pagination.items,
        "pagination": pagination,
        "search_query": search_query,
        "sort_by": sort_by,
        "order": order,
    }


def get_patient_payments_context(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    payment_sort = request.args.get("payment_sort", "date")
    payment_order = request.args.get("payment_order", "desc")

    patient_payments = Payment.query.filter_by(patient_id=patient.id).all()

    sort_key_map = {
        "id": lambda payment: payment.id,
        "date": lambda payment: payment.payment_date,
        "amount": lambda payment: payment.amount,
        "allocated": lambda payment: payment.allocated_amount,
        "credit": lambda payment: payment.unallocated_amount,
    }

    sort_key = sort_key_map.get(payment_sort, sort_key_map["date"])

    patient_payments = sorted(
        patient_payments,
        key=sort_key,
        reverse=payment_order != "asc",
    )

    return {
        "patient": patient,
        "patient_payments": patient_payments,
        "payment_sort": payment_sort,
        "payment_order": payment_order,
    }


def get_patient_invoices_context(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    invoice_sort = request.args.get("invoice_sort", "date")
    invoice_order = request.args.get("invoice_order", "desc")

    patient_invoices = (
        Invoice.query
        .filter_by(patient_id=patient.id)
        .join(Invoice.appointment)
        .all()
    )

    sort_key_map = {
        "id": lambda invoice: invoice.id,
        "date": lambda invoice: invoice.appointment_date,
        "patient": lambda invoice: (invoice.patient.first_name, invoice.patient.last_name),
        "treatments": lambda invoice: invoice.treatments_count,
        "total": lambda invoice: invoice.total_amount,
        "payments": lambda invoice: invoice.total_paid,
        "outstanding": lambda invoice: invoice.balance,
        "status": lambda invoice: invoice.status,
    }

    sort_key = sort_key_map.get(invoice_sort, sort_key_map["date"])

    patient_invoices = sorted(
        patient_invoices,
        key=sort_key,
        reverse=invoice_order != "asc",
    )

    return {
        "patient": patient,
        "invoices": patient_invoices,
        "invoice_sort": invoice_sort,
        "invoice_order": invoice_order,
    }


@patients_bp.route("/patients")
@role_required("admin", "doctor", "receptionist")
def patients():
    current_app.logger.info("Patients page opened")

    try:
        context = get_patients_context()
        return render_template("patients/patients.html", **context)

    except Exception:
        current_app.logger.exception("Error while loading patients page")
        return "Error Loading PatientsPage", 500


@patients_bp.route("/patients/table")
@role_required("admin", "doctor", "receptionist")
def patients_table():
    current_app.logger.info("Patients table partial requested")

    try:
        context = get_patients_context()
        return render_template("partials/_patients_table.html", **context)

    except Exception:
        current_app.logger.exception("Error while loading patients table")
        return "Error Loading PatientsTable", 500


@patients_bp.route("/patients/add", methods=["GET", "POST"])
@role_required("admin", "receptionist")
def add_patient():
    if request.method == "POST":
        patient_data, patient_error = parse_patient_data(request.form)

        if patient_error:
            return render_template(
                "patients/add_patient.html",
                error_message=patient_error,
            ), 400

        try:
            new_patient = Patient(**patient_data)

            db.session.add(new_patient)
            db.session.commit()

            return redirect(url_for("patients.patients"))
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Failed to add patient")
            return render_template(
                "patients/add_patient.html",
                error_message="Failed to save patient database record. Please try again.",
            ), 500

    return render_template("patients/add_patient.html")


@patients_bp.route("/patients/<int:patient_id>")
@role_required("admin", "doctor", "receptionist")
def patient_detail(patient_id):
    current_app.logger.info(f"Patient detail page opened | patient_id={patient_id}")

    try:
        patient = Patient.query.get_or_404(patient_id)

        appointment_sort = request.args.get("appointment_sort", "date")
        appointment_order = request.args.get("appointment_order", "desc")

        treatment_sort = request.args.get("treatment_sort", "date")
        treatment_order = request.args.get("treatment_order", "desc")

        payment_context = get_patient_payments_context(patient.id)
        invoice_context = get_patient_invoices_context(patient.id)

        active_tab = request.args.get("tab", "appointments")

        appointment_sort_columns = {
            "id": Appointment.id,
            "date": Appointment.appointment_date,
            "reason": Appointment.reason,
            "status": Appointment.status,
        }

        appointment_sort_column = appointment_sort_columns.get(
            appointment_sort,
            Appointment.appointment_date,
        )

        appointments_query = Appointment.query.filter_by(patient_id=patient.id)

        if appointment_order == "asc":
            appointments_query = appointments_query.order_by(appointment_sort_column.asc())
        else:
            appointments_query = appointments_query.order_by(appointment_sort_column.desc())

        patient_appointments = appointments_query.all()

        treatment_sort_columns = {
            "id": Treatment.id,
            "date": Treatment.treatment_date,
            "procedure_type": Treatment.procedure_type,
            "tooth_number": Treatment.tooth_number,
        }

        treatment_sort_column = treatment_sort_columns.get(
            treatment_sort,
            Treatment.treatment_date,
        )

        treatments_query = (
            Treatment.query
            .join(Appointment)
            .filter(Appointment.patient_id == patient.id)
        )

        if treatment_order == "asc":
            treatments_query = treatments_query.order_by(treatment_sort_column.asc())
        else:
            treatments_query = treatments_query.order_by(treatment_sort_column.desc())

        patient_treatments = treatments_query.all()
        
        patient_invoices = (
                Invoice.query
                .filter_by(patient_id=patient.id)
                .join(Invoice.appointment)
                .order_by(Appointment.appointment_date.desc(), Invoice.id.desc())
                .all()
            )

        total_cost_sum = patient.total_invoice_amount
        total_paid_sum = patient.total_payments_amount
        total_remaining_sum = patient.outstanding_amount
        credit_amount = patient.credit_amount

        patient_files = sorted(patient.files, key=lambda f: f.upload_date, reverse=True)

        return render_template(
            "patients/patient_detail.html",
            patient=patient,
            patient_appointments=patient_appointments,
            patient_treatments=patient_treatments,
            patient_payments=payment_context["patient_payments"],
            invoices=invoice_context["invoices"],
            patient_files=patient_files,
            total_cost_sum=total_cost_sum,
            total_paid_sum=total_paid_sum,
            total_remaining_sum=total_remaining_sum,
            credit_amount=credit_amount,
            appointment_sort=appointment_sort,
            appointment_order=appointment_order,
            treatment_sort=treatment_sort,
            treatment_order=treatment_order,
            payment_sort=payment_context["payment_sort"],
            payment_order=payment_context["payment_order"],
            invoice_sort=invoice_context["invoice_sort"],
            invoice_order=invoice_context["invoice_order"],
            active_tab=active_tab,
        )

    except Exception:
        current_app.logger.exception(
            f"Error while loading patient detail | patient_id={patient_id}"
        )
        return "Error Loading PatientsInfo", 500


@patients_bp.route("/patients/<int:patient_id>/payments-table")
@role_required("admin", "doctor", "receptionist")
def patient_payments_table(patient_id):
    context = get_patient_payments_context(patient_id)

    return render_template(
        "partials/_patient_payments_table.html",
        **context,
    )


@patients_bp.route("/patients/<int:patient_id>/invoices-table")
@role_required("admin", "doctor", "receptionist")
def patient_invoices_table(patient_id):
    context = get_patient_invoices_context(patient_id)

    return render_template(
        "partials/_patient_invoices_table.html",
        **context,
    )


@patients_bp.route("/patients/<int:patient_id>/appointments-table")
@role_required("admin", "doctor", "receptionist")
def patient_appointments_table(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    appointment_sort = request.args.get("appointment_sort", "date")
    appointment_order = request.args.get("appointment_order", "desc")

    sort_columns = {
        "id": Appointment.id,
        "date": Appointment.appointment_date,
        "reason": Appointment.reason,
        "status": Appointment.status,
    }

    sort_column = sort_columns.get(appointment_sort, Appointment.appointment_date)

    query = Appointment.query.filter_by(patient_id=patient.id)

    if appointment_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    patient_appointments = query.all()

    return render_template(
        "partials/_patient_appointments_table.html",
        patient=patient,
        patient_appointments=patient_appointments,
        appointment_sort=appointment_sort,
        appointment_order=appointment_order,
    )


@patients_bp.route("/patients/<int:patient_id>/treatments-table")
@role_required("admin", "doctor", "receptionist")
def patient_treatments_table(patient_id):
    patient = Patient.query.get_or_404(patient_id)

    treatment_sort = request.args.get("treatment_sort", "date")
    treatment_order = request.args.get("treatment_order", "desc")

    sort_columns = {
        "id": Treatment.id,
        "date": Treatment.treatment_date,
        "procedure_type": Treatment.procedure_type,
        "tooth_number": Treatment.tooth_number,
    }

    sort_column = sort_columns.get(treatment_sort, Treatment.treatment_date)

    query = (
        Treatment.query
        .join(Appointment)
        .filter(Appointment.patient_id == patient.id)
    )

    if treatment_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    patient_treatments = query.all()

    return render_template(
        "partials/_patient_treatments_table.html",
        patient=patient,
        patient_treatments=patient_treatments,
        treatment_sort=treatment_sort,
        treatment_order=treatment_order,
    )


@patients_bp.route("/patients/<int:patient_id>/edit", methods=["GET", "POST"])
@role_required("admin", "doctor", "receptionist")
def edit_patient(patient_id):
    current_app.logger.info(f"Edit patient page/request | patient_id={patient_id}")

    try:
        patient = Patient.query.get_or_404(patient_id)

        if request.method == "POST":
            patient_data, patient_error = parse_patient_data(request.form)

            if patient_error:
                return render_template(
                    "patients/edit_patient.html",
                    patient=patient,
                    mode="edit",
                    error_message=patient_error,
                ), 400

            for field, value in patient_data.items():
                setattr(patient, field, value)

            db.session.commit()

            current_app.logger.info(
                f"Patient updated successfully | patient_id={patient.id}"
            )
            return redirect(url_for("patients.patient_detail", patient_id=patient.id))

        return render_template(
            "patients/edit_patient.html",
            patient=patient,
            mode="edit",
        )

    except Exception:
        db.session.rollback()
        current_app.logger.exception(f"Failed to edit patient | patient_id={patient_id}")
        return "Failed to edit patient", 500


@patients_bp.route("/patients/<int:patient_id>/view")
@role_required("admin", "doctor", "receptionist")
def view_patient(patient_id):
    current_app.logger.info(f"View patient page opened | patient_id={patient_id}")

    try:
        patient = Patient.query.get_or_404(patient_id)

        return render_template(
            "patients/edit_patient.html",
            patient=patient,
            mode="view",
        )

    except Exception:
        current_app.logger.exception(f"Failed to view patient | patient_id={patient_id}")
        return "Failed to view patient", 500


@patients_bp.route("/patients/<int:patient_id>/delete", methods=["GET", "POST"])
@role_required("admin")
def delete_patient(patient_id):
    current_app.logger.warning(f"Delete patient page/request | patient_id={patient_id}")

    try:
        patient = Patient.query.get_or_404(patient_id)

        if patient.appointments:
            return render_template(
                "error_message.html",
                title="Action Not Allowed",
                message=(
                    "Cannot delete this patient because they have appointments "
                    "linked to their medical history."
                ),
                back_url=url_for("patients.patient_detail", patient_id=patient.id),
            ), 403

        if request.method == "POST":
            import os
            for patient_file in patient.files:
                disk_path = os.path.join(current_app.static_folder, patient_file.filepath)
                if os.path.exists(disk_path):
                    try:
                        os.remove(disk_path)
                    except Exception:
                        current_app.logger.exception(f"Failed to remove file from disk during patient delete: {disk_path}")
            
            db.session.delete(patient)
            db.session.commit()

            current_app.logger.info(
                f"Patient deleted successfully | patient_id={patient_id}"
            )
            return redirect(url_for("patients.patients"))

        return render_template("patients/delete_patient.html", patient=patient)

    except Exception:
        db.session.rollback()
        current_app.logger.exception(f"Failed to delete patient | patient_id={patient_id}")
        return render_template(
            "error_message.html",
            title="Error",
            message="Failed to delete patient.",
            back_url=url_for("patients.patients"),
        ), 500


@patients_bp.route("/patients/<int:patient_id>/portal/create", methods=["POST"])
@role_required("admin", "receptionist")
def create_portal_account(patient_id):
    current_app.logger.info(f"Creating patient portal account for patient_id={patient_id}")
    try:
        patient = Patient.query.get_or_404(patient_id)
        if patient.user:
            flash("Patient already has a portal account.", "warning")
            return redirect(url_for("patients.patient_detail", patient_id=patient.id))

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Username and password are required.", "danger")
            return redirect(url_for("patients.patient_detail", patient_id=patient.id))

        if len(username) > 80:
            flash("Username cannot exceed 80 characters.", "danger")
            return redirect(url_for("patients.patient_detail", patient_id=patient.id))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return redirect(url_for("patients.patient_detail", patient_id=patient.id))

        from models import User
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists. Please choose a different one.", "danger")
            return redirect(url_for("patients.patient_detail", patient_id=patient.id))

        new_user = User(
            username=username,
            role="patient",
            first_name=patient.first_name,
            last_name=patient.last_name,
            patient_id=patient.id,
            plain_password=password
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash(f"Portal account created successfully for patient: {patient.first_name}. Username: {username}", "success")
        return redirect(url_for("patients.patient_detail", patient_id=patient.id))

    except Exception:
        db.session.rollback()
        current_app.logger.exception(f"Failed to create portal account for patient_id={patient_id}")
        flash("Failed to create portal account due to a database error.", "danger")
        return redirect(url_for("patients.patient_detail", patient_id=patient_id))


@patients_bp.route("/patients/<int:patient_id>/portal/delete", methods=["POST"])
@role_required("admin", "receptionist")
def delete_portal_account(patient_id):
    current_app.logger.warning(f"Deleting patient portal account for patient_id={patient_id}")
    try:
        patient = Patient.query.get_or_404(patient_id)
        if not patient.user:
            flash("Patient does not have a portal account.", "warning")
            return redirect(url_for("patients.patient_detail", patient_id=patient.id))

        db.session.delete(patient.user)
        db.session.commit()

        flash("Portal account access deleted successfully.", "success")
        return redirect(url_for("patients.patient_detail", patient_id=patient.id))

    except Exception:
        db.session.rollback()
        current_app.logger.exception(f"Failed to delete portal account for patient_id={patient_id}")
        flash("Failed to delete portal account.", "danger")
        return redirect(url_for("patients.patient_detail", patient_id=patient_id))


@patients_bp.route("/patients/<int:patient_id>/files/upload", methods=["POST"])
@role_required("admin", "doctor", "receptionist")
def upload_patient_file(patient_id):
    import os
    import uuid
    from werkzeug.utils import secure_filename
    
    patient = Patient.query.get_or_404(patient_id)
    
    if "file" not in request.files:
        flash("No file part", "danger")
        return redirect(url_for("patients.patient_detail", patient_id=patient_id, tab="files"))
        
    file = request.files["file"]
    notes = request.form.get("notes", "").strip()
    category = request.form.get("category", "General").strip()
    
    if file.filename == "":
        flash("No selected file", "danger")
        return redirect(url_for("patients.patient_detail", patient_id=patient_id, tab="files"))
        
    if file:
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        
        upload_dir = os.path.join(current_app.static_folder, "uploads", "patients")
        os.makedirs(upload_dir, exist_ok=True)
        
        filepath = os.path.join(upload_dir, unique_filename)
        file.save(filepath)
        
        relative_path = f"uploads/patients/{unique_filename}"
        
        new_file = PatientFile(
            patient_id=patient_id,
            filename=filename,
            filepath=relative_path,
            filetype=file.content_type,
            notes=notes,
            category=category
        )
        
        try:
            db.session.add(new_file)
            db.session.commit()
            flash("File uploaded successfully.", "success")
        except Exception:
            db.session.rollback()
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception:
                    pass
            current_app.logger.exception("Failed to save PatientFile to database")
            flash("Failed to save file metadata to database.", "danger")
            
        return redirect(url_for("patients.patient_detail", patient_id=patient_id, tab="files"))


@patients_bp.route("/patients/<int:patient_id>/files/<int:file_id>/delete", methods=["POST"])
@role_required("admin", "doctor", "receptionist")
def delete_patient_file(patient_id, file_id):
    import os
    
    patient = Patient.query.get_or_404(patient_id)
    patient_file = PatientFile.query.get_or_404(file_id)
    
    if patient_file.patient_id != patient.id:
        flash("Unauthorized operation.", "danger")
        return redirect(url_for("patients.patient_detail", patient_id=patient_id, tab="files"))
        
    disk_path = os.path.join(current_app.static_folder, patient_file.filepath)
    if os.path.exists(disk_path):
        try:
            os.remove(disk_path)
        except Exception:
            current_app.logger.exception(f"Failed to remove file from disk: {disk_path}")
            
    try:
        db.session.delete(patient_file)
        db.session.commit()
        flash("File deleted successfully.", "success")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Failed to delete PatientFile from database")
        flash("Failed to delete file from database.", "danger")
        
    return redirect(url_for("patients.patient_detail", patient_id=patient_id, tab="files"))
