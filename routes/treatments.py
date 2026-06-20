from flask import Blueprint, current_app, render_template, request, redirect, url_for

from models import db, Appointment, Treatment
from services.invoice_service import sync_invoice_for_appointment
from services.payment_service import allocate_patient_payments_to_invoices
from utils.constants import TREATMENT_PRICES, TREATMENT_PROCEDURE_TYPES
from utils.auth_helper import role_required


treatments_bp = Blueprint("treatments", __name__)


@treatments_bp.route("/appointments/<int:appointment_id>/session")
@role_required("admin", "doctor")
def appointment_session(appointment_id):
    current_app.logger.info(f"Appointment session opened | appointment_id={appointment_id}")

    try:
        appointment = Appointment.query.get_or_404(appointment_id)

        treatments = (
            Treatment.query
            .filter_by(appointment_id=appointment.id)
            .order_by(Treatment.id.desc())
            .all()
        )

        previous_treatments = (
            Treatment.query
            .join(Appointment)
            .filter(Appointment.patient_id == appointment.patient_id)
            .filter(Treatment.appointment_id != appointment.id)
            .order_by(Treatment.treatment_date.desc(), Treatment.id.desc())
            .all()
        )

        total_cost_sum = appointment.invoice_total
        total_paid_sum = appointment.total_paid
        total_remaining_sum = appointment.balance
        credit_amount = appointment.credit

        return render_template(
            "appointments/appointment_session.html",
            appointment=appointment,
            patient=appointment.patient,
            treatments=treatments,
            total_cost_sum=total_cost_sum,
            total_paid_sum=total_paid_sum,
            total_remaining_sum=total_remaining_sum,
            credit_amount=credit_amount,
            previous_treatments=previous_treatments,
        )

    except Exception:
        current_app.logger.exception(
            f"Failed to open appointment session | appointment_id={appointment_id}"
        )
        return render_template(
            "error_message.html",
            title="Error",
            message="Failed to open appointment session.",
            back_url=url_for("appointments.appointments"),
        ), 500


@treatments_bp.route("/appointments/<int:appointment_id>/treatments/add", methods=["GET", "POST"])
@role_required("admin", "doctor")
def add_treatment_to_appointment(appointment_id):
    current_app.logger.info(f"Add treatment to appointment | appointment_id={appointment_id}")

    try:
        appointment = Appointment.query.get_or_404(appointment_id)

        if appointment.status != "Scheduled":
            return render_template(
                "error_message.html",
                title="Action Not Allowed",
                message="Cannot add treatment because this appointment session is closed or cancelled.",
                back_url=url_for("treatments.appointment_session", appointment_id=appointment.id),
            ), 403

        if request.method == "POST":
            treatment_date = appointment.appointment_date
            procedure_type = request.form.get("procedure_type", "").strip()

            if procedure_type not in TREATMENT_PROCEDURE_TYPES:
                return render_template(
                    "treatments/add_treatment.html",
                    appointment=appointment,
                    patient=appointment.patient,
                    treatment_prices=dict(TREATMENT_PRICES),
                    error_message="Invalid treatment procedure type.",
                ), 400

            tooth_number = request.form.get("tooth_number", "").strip()
            if len(tooth_number) > 50:
                return render_template(
                    "treatments/add_treatment.html",
                    appointment=appointment,
                    patient=appointment.patient,
                    treatment_prices=dict(TREATMENT_PRICES),
                    error_message="Tooth number cannot exceed 50 characters.",
                ), 400

            notes = request.form.get("notes", "").strip()

            total_cost = TREATMENT_PRICES[procedure_type]

            new_treatment = Treatment(
                appointment_id=appointment.id,
                treatment_date=treatment_date,
                procedure_type=procedure_type,
                tooth_number=tooth_number,
                notes=notes,
                total_cost=total_cost,
            )

            db.session.add(new_treatment)
            db.session.flush()

            sync_invoice_for_appointment(appointment)
            allocate_patient_payments_to_invoices(appointment.patient_id)

            db.session.commit()

            current_app.logger.info(
                f"Treatment added successfully | treatment_id={new_treatment.id}, appointment_id={appointment.id}"
            )

            return redirect(
                url_for("treatments.appointment_session", appointment_id=appointment.id)
            )

        return render_template(
            "treatments/add_treatment.html",
            appointment=appointment,
            patient=appointment.patient,
            treatment_prices=dict(TREATMENT_PRICES),
        )

    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            f"Failed to add treatment to appointment | appointment_id={appointment_id}"
        )
        return render_template(
            "error_message.html",
            title="Error",
            message="Failed to add treatment.",
            back_url=url_for("treatments.appointment_session", appointment_id=appointment_id),
        ), 500


@treatments_bp.route("/appointments/<int:appointment_id>/end-session", methods=["POST"])
@role_required("admin", "doctor")
def end_appointment_session(appointment_id):
    current_app.logger.info(f"End appointment session request | appointment_id={appointment_id}")

    try:
        appointment = Appointment.query.get_or_404(appointment_id)

        if appointment.status != "Scheduled":
            return render_template(
                "error_message.html",
                title="Action Not Allowed",
                message="Only scheduled appointments can be ended.",
                back_url=url_for("treatments.appointment_session", appointment_id=appointment.id),
            ), 400

        appointment.status = "Done"
        db.session.commit()

        current_app.logger.info(
            f"Appointment session ended successfully | appointment_id={appointment.id}"
        )

        return redirect(
            url_for("treatments.appointment_session", appointment_id=appointment.id)
        )

    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            f"Failed to end appointment session | appointment_id={appointment_id}"
        )
        return render_template(
            "error_message.html",
            title="Error",
            message="Failed to end appointment session.",
            back_url=url_for("treatments.appointment_session", appointment_id=appointment_id),
        ), 500


@treatments_bp.route("/appointments/<int:appointment_id>/reopen-session", methods=["POST"])
@role_required("admin", "doctor")
def reopen_appointment_session(appointment_id):
    current_app.logger.info(f"Reopen appointment session request | appointment_id={appointment_id}")
    try:
        appointment = Appointment.query.get_or_404(appointment_id)

        if appointment.status != "Done":
            return render_template(
                "error_message.html",
                title="Action Not Allowed",
                message="Only completed appointments can be reopened.",
                back_url=url_for("treatments.appointment_session", appointment_id=appointment.id),
            ), 400

        if appointment.invoice and appointment.invoice.total_paid > 0:
            return render_template(
                "error_message.html",
                title="Action Not Allowed",
                message="Cannot reopen this session because payments have already been made towards its invoice. Please remove payments first.",
                back_url=url_for("treatments.appointment_session", appointment_id=appointment.id),
            ), 403

        appointment.status = "Scheduled"
        db.session.commit()

        current_app.logger.info(
            f"Appointment session reopened successfully | appointment_id={appointment.id}"
        )

        return redirect(
            url_for("treatments.appointment_session", appointment_id=appointment.id)
        )

    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            f"Failed to reopen appointment session | appointment_id={appointment_id}"
        )
        return render_template(
            "error_message.html",
            title="Error",
            message="Failed to reopen appointment session.",
            back_url=url_for("treatments.appointment_session", appointment_id=appointment_id),
        ), 500


@treatments_bp.route("/patients/<int:patient_id>/treatments/add")
@role_required("admin", "doctor")
def add_treatment(patient_id):
    current_app.logger.warning(
        f"Legacy add treatment route opened | patient_id={patient_id}"
    )

    return (
        "Treatments must be added from an appointment session.",
        400,
    )


@treatments_bp.route("/treatments/<int:treatment_id>/edit", methods=["GET", "POST"])
@role_required("admin", "doctor")
def edit_treatment(treatment_id):
    current_app.logger.info(f"Edit treatment page/request | treatment_id={treatment_id}")

    try:
        treatment = Treatment.query.get_or_404(treatment_id)

        if treatment.appointment.status != "Scheduled" and request.method == "POST":
            return render_template(
                "error_message.html",
                title="Action Not Allowed",
                message="Cannot edit this treatment because the appointment session is closed or cancelled.",
                back_url=url_for(
                    "treatments.appointment_session",
                    appointment_id=treatment.appointment_id,
                ),
            ), 403

        if request.method == "POST":
            treatment.treatment_date = treatment.appointment.appointment_date

            procedure_type = request.form.get("procedure_type", "").strip()

            if procedure_type not in TREATMENT_PROCEDURE_TYPES:
                return render_template(
                    "treatments/edit_treatment.html",
                    treatment=treatment,
                    appointment=treatment.appointment,
                    patient=treatment.appointment.patient,
                    mode="edit",
                    treatment_prices=dict(TREATMENT_PRICES),
                    error_message="Invalid treatment procedure type.",
                ), 400

            tooth_number = request.form.get("tooth_number", "").strip()
            if len(tooth_number) > 50:
                return render_template(
                    "treatments/edit_treatment.html",
                    treatment=treatment,
                    appointment=treatment.appointment,
                    patient=treatment.appointment.patient,
                    mode="edit",
                    treatment_prices=dict(TREATMENT_PRICES),
                    error_message="Tooth number cannot exceed 50 characters.",
                ), 400

            treatment.procedure_type = procedure_type
            treatment.tooth_number = tooth_number
            treatment.notes = request.form.get("notes", "").strip()
            treatment.total_cost = TREATMENT_PRICES[procedure_type]

            db.session.flush()

            sync_invoice_for_appointment(treatment.appointment)
            allocate_patient_payments_to_invoices(treatment.appointment.patient_id)

            db.session.commit()

            current_app.logger.info(
                f"Treatment updated successfully | treatment_id={treatment.id}"
            )

            return redirect(
                url_for(
                    "treatments.appointment_session",
                    appointment_id=treatment.appointment_id,
                )
            )

        return render_template(
            "treatments/edit_treatment.html",
            treatment=treatment,
            appointment=treatment.appointment,
            patient=treatment.appointment.patient,
            mode="edit",
            treatment_prices=dict(TREATMENT_PRICES),
        )

    except Exception:
        db.session.rollback()
        current_app.logger.exception(f"Failed to edit treatment | treatment_id={treatment_id}")
        return render_template(
            "error_message.html",
            title="Error",
            message="Failed to edit treatment.",
            back_url=url_for("appointments.appointments"),
        ), 500


@treatments_bp.route("/treatments/<int:treatment_id>/view")
@role_required("admin", "doctor")
def view_treatment(treatment_id):
    current_app.logger.info(f"View treatment page opened | treatment_id={treatment_id}")

    try:
        treatment = Treatment.query.get_or_404(treatment_id)

        return render_template(
            "treatments/edit_treatment.html",
            treatment=treatment,
            appointment=treatment.appointment,
            patient=treatment.appointment.patient,
            mode="view",
            treatment_prices=dict(TREATMENT_PRICES),
        )

    except Exception:
        current_app.logger.exception(f"Failed to view treatment | treatment_id={treatment_id}")
        return render_template(
            "error_message.html",
            title="Error",
            message="Failed to view treatment.",
            back_url=url_for("appointments.appointments"),
        ), 500


@treatments_bp.route("/treatments/<int:treatment_id>/delete", methods=["GET", "POST"])
@role_required("admin", "doctor")
def delete_treatment(treatment_id):
    current_app.logger.warning(f"Delete treatment page/request | treatment_id={treatment_id}")

    try:
        treatment = Treatment.query.get_or_404(treatment_id)
        appointment = treatment.appointment
        appointment_id = treatment.appointment_id
        patient_id = treatment.appointment.patient_id

        if treatment.appointment.status != "Scheduled":
            return render_template(
                "error_message.html",
                title="Action Not Allowed",
                message="Cannot delete this treatment because the appointment session is closed or cancelled.",
                back_url=url_for("treatments.appointment_session", appointment_id=appointment_id),
            ), 403

        if request.method == "POST":
            db.session.delete(treatment)
            db.session.flush()

            sync_invoice_for_appointment(appointment)
            allocate_patient_payments_to_invoices(patient_id)

            db.session.commit()

            current_app.logger.info(
                f"Treatment deleted successfully | treatment_id={treatment_id}"
            )
            return redirect(
                url_for("treatments.appointment_session", appointment_id=appointment_id)
            )

        return render_template("treatments/delete_treatment.html", treatment=treatment)

    except Exception:
        db.session.rollback()
        current_app.logger.exception(f"Failed to delete treatment | treatment_id={treatment_id}")
        return render_template(
            "error_message.html",
            title="Error",
            message="Failed to delete treatment.",
            back_url=url_for("appointments.appointments"),
        ), 500