from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash
from models import db, PatientFile, Patient
from utils.auth_helper import role_required

archive_bp = Blueprint("archive", __name__)

@archive_bp.route("/archive")
@role_required("admin", "doctor", "receptionist")
def list_archive():
    current_app.logger.info("General Document Archive opened")
    search_query = request.args.get("search", "").strip()
    selected_category = request.args.get("category", "").strip()
    selected_client_id = request.args.get("client_id", "", type=int)
    
    query = PatientFile.query.join(Patient)
    
    if search_query:
        query = query.filter(
            (PatientFile.filename.ilike(f"%{search_query}%")) |
            (PatientFile.notes.ilike(f"%{search_query}%"))
        )
        
    if selected_category:
        query = query.filter(PatientFile.category == selected_category)
        
    if selected_client_id:
        query = query.filter(PatientFile.patient_id == selected_client_id)
        
    files = query.order_by(PatientFile.upload_date.desc()).all()
    clients = Patient.query.order_by(Patient.first_name.asc(), Patient.last_name.asc()).all()
    
    categories = ["Design Plans", "Contracts", "Invoices", "Site Images", "General"]
    
    return render_template(
        "archive/list.html",
        files=files,
        clients=clients,
        categories=categories,
        search_query=search_query,
        selected_category=selected_category,
        selected_client_id=selected_client_id
    )
