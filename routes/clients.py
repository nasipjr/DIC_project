import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app
from models import db, Client, ClientFile, Invoice, Payment
from utils.auth_helper import role_required
from werkzeug.utils import secure_filename

clients_bp = Blueprint("clients", __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')

@clients_bp.route("/clients")
@role_required("admin")
def list_clients():
    search_query = request.args.get("search", "").strip()
    query = Client.query
    
    if search_query:
        query = query.filter(
            (Client.name.ilike(f"%{search_query}%")) |
            (Client.phone.ilike(f"%{search_query}%")) |
            (Client.address.ilike(f"%{search_query}%"))
        )
        
    clients_raw = query.order_by(Client.name.asc()).all()
    
    # Enrich clients with statistics
    clients = []
    for client in clients_raw:
        # Match invoices by client name
        invoice_count = Invoice.query.filter_by(client_name=client.name).count()
        file_count = ClientFile.query.filter_by(client_id=client.id).count()
        
        clients.append({
            "id": client.id,
            "name": client.name,
            "phone": client.phone or "-",
            "address": client.address or "-",
            "invoice_count": invoice_count,
            "file_count": file_count,
            "created_at": client.created_at
        })
        
    return render_template(
        "clients/list.html",
        clients=clients,
        search_query=search_query
    )

@clients_bp.route("/clients/add", methods=["POST"])
@role_required("admin")
def add_client():
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip() or None
    address = request.form.get("address", "").strip() or None
    
    if not name:
        flash("Client name is required.", "danger")
        return redirect(url_for("clients.list_clients"))
        
    # Check if client name is unique
    existing = Client.query.filter_by(name=name).first()
    if existing:
        flash(f"A client with name '{name}' already exists.", "danger")
        return redirect(url_for("clients.list_clients"))
        
    try:
        new_client = Client(name=name, phone=phone, address=address)
        db.session.add(new_client)
        db.session.commit()
        flash(f"Client '{name}' added successfully.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Failed to add client: {e}")
        flash("Failed to add client due to a database error.", "danger")
        
    return redirect(url_for("clients.list_clients"))

@clients_bp.route("/clients/<int:client_id>")
@role_required("admin")
def view_client(client_id):
    client = Client.query.get_or_404(client_id)
    
    # Retrieve linked invoices
    invoices = Invoice.query.filter_by(client_name=client.name).order_by(Invoice.issue_date.desc()).all()
    
    # Retrieve files
    files = ClientFile.query.filter_by(client_id=client.id).order_by(ClientFile.uploaded_at.desc()).all()
    
    # Retrieve payments
    payments = Payment.query.filter_by(client_id=client.id).order_by(Payment.payment_date.desc()).all()
    
    # Financial statistics
    total_invoiced = client.total_invoiced
    total_paid = client.total_paid
    credit_balance = client.credit
    outstanding_balance = client.outstanding
    
    return render_template(
        "clients/profile.html",
        client=client,
        invoices=invoices,
        files=files,
        payments=payments,
        total_invoiced=total_invoiced,
        total_paid=total_paid,
        credit_balance=credit_balance,
        outstanding_balance=outstanding_balance,
        file_count=len(files)
    )

@clients_bp.route("/clients/<int:client_id>/upload", methods=["POST"])
@role_required("admin")
def upload_file(client_id):
    client = Client.query.get_or_404(client_id)
    
    if 'file' not in request.files:
        flash("No file part selected.", "danger")
        return redirect(url_for("clients.view_client", client_id=client.id))
        
    file = request.files['file']
    if file.filename == '':
        flash("No file selected.", "danger")
        return redirect(url_for("clients.view_client", client_id=client.id))
        
    if file:
        filename = secure_filename(file.filename)
        # Prevent completely blank filename
        if not filename:
            filename = f"uploaded_file_{client_id}"
            
        client_dir = os.path.join(UPLOAD_FOLDER, 'clients', str(client.id))
        os.makedirs(client_dir, exist_ok=True)
        
        # Check for duplicate filenames and rename if necessary
        base_name, extension = os.path.splitext(filename)
        counter = 1
        final_filename = filename
        while os.path.exists(os.path.join(client_dir, final_filename)):
            final_filename = f"{base_name}_{counter}{extension}"
            counter += 1
            
        filepath = os.path.join(client_dir, final_filename)
        
        try:
            file.save(filepath)
            file_size = os.path.getsize(filepath)
            
            # Save file record to database
            relative_path = os.path.join('clients', str(client.id), final_filename).replace('\\', '/')
            new_file = ClientFile(
                client_id=client.id,
                filename=final_filename,
                filepath=relative_path,
                file_size=file_size
            )
            db.session.add(new_file)
            db.session.commit()
            
            flash(f"File '{final_filename}' uploaded successfully.", "success")
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception(f"Failed to upload client file: {e}")
            flash("Failed to upload file due to server error.", "danger")
            
    return redirect(url_for("clients.view_client", client_id=client.id))

@clients_bp.route("/clients/<int:client_id>/file/download/<int:file_id>")
@role_required("admin")
def download_file(client_id, file_id):
    client = Client.query.get_or_404(client_id)
    client_file = ClientFile.query.filter_by(id=file_id, client_id=client.id).first_or_404()
    
    client_dir = os.path.join(UPLOAD_FOLDER, 'clients', str(client.id))
    return send_from_directory(client_dir, client_file.filename, as_attachment=True)

@clients_bp.route("/clients/<int:client_id>/file/delete/<int:file_id>", methods=["POST"])
@role_required("admin")
def delete_file(client_id, file_id):
    client = Client.query.get_or_404(client_id)
    client_file = ClientFile.query.filter_by(id=file_id, client_id=client.id).first_or_404()
    
    client_dir = os.path.join(UPLOAD_FOLDER, 'clients', str(client.id))
    filepath = os.path.join(client_dir, client_file.filename)
    
    try:
        # Delete from disk if it exists
        if os.path.exists(filepath):
            os.remove(filepath)
            
        # Delete from database
        db.session.delete(client_file)
        db.session.commit()
        flash("File deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Failed to delete client file: {e}")
        flash("Failed to delete file from system.", "danger")
        
    return redirect(url_for("clients.view_client", client_id=client.id))
