# Dental Clinic Management System

A Flask web application for managing the daily workflow of a dental clinic. It helps organize patients, appointments, treatment sessions, invoices, and payments in one place.

This project is mainly intended for learning, academic work, and continued improvement.

## What the System Does

The application supports the main clinic workflow:

1. Register and manage patients.
2. Schedule patient appointments.
3. Start an appointment session and add treatments.
4. End the session to save the appointment as medical history.
5. Generate and track invoices.
6. Record patient payments and allocate them to unpaid invoices.

## Main Features

- Dashboard with financial and operational summaries.
- Patient management with add, edit, detail, search, and sorting views.
- Appointment scheduling, editing, filtering, sorting, and status tracking.
- Treatment session workflow for adding, editing, and deleting treatments before completion.
- Completed appointments become read-only medical records.
- Invoice list and invoice detail pages.
- Payment recording at the patient level.
- Automatic allocation of payments to outstanding invoices.
- Patient detail page with payments, invoices, treatments, and financial summary.
- AJAX-style appointment table updates for searching, filtering, and sorting without a full page refresh.

## Appointment Workflow

```text
Scheduled appointment
        |
        v
Add, edit, or delete treatments
        |
        v
End session
        |
        v
Done appointment / medical record
```

When an appointment is still scheduled:

- Treatments can be added.
- Treatments can be edited.
- Treatments can be deleted.
- The appointment can be edited or cancelled when allowed.
- The session can be ended after treatment data is added.

When an appointment is marked as done:

- Treatment data becomes read-only.
- Treatments cannot be added, edited, or deleted.
- The appointment should not be deleted because it represents medical history.
- Payments can still be added if the patient has an outstanding balance.

## Payment and Invoice Logic

Payments are recorded at the patient level, not directly on a single appointment form.

When a payment is added, `services/payment_service.py` allocates it to the patient's unpaid invoices. The system tracks:

- Invoice total.
- Paid amount.
- Remaining amount.
- Invoice status.
- Allocated payment amount.
- Patient credit when a payment is larger than the outstanding balance.

## Technologies

- Python
- Flask
- Flask-SQLAlchemy
- MySQL
- PyMySQL
- HTML
- CSS
- Bootstrap
- JavaScript

## Project Structure

```text
Dental Clinic MS Flask/
|-- app.py
|-- models.py
|-- settings.py
|-- setup.py
|-- requirements.txt
|-- README.md
|-- .env.example
|-- .gitignore
|
|-- routes/
|   |-- dashboard.py
|   |-- patients.py
|   |-- appointments.py
|   |-- treatments.py
|   |-- payments.py
|   `-- invoices.py
|
|-- services/
|   `-- payment_service.py
|
|-- utils/
|   |-- constants.py
|   |-- validators.py
|   `-- logging_config.py
|
|-- templates/
|   |-- base.html
|   |-- error_message.html
|   |-- dashboard/
|   |-- patients/
|   |-- appointments/
|   |-- treatments/
|   |-- payments/
|   |-- invoices/
|   |-- partials/
|   `-- unused/
|
|-- static/
|   |-- styles.css
|   `-- assets/
|
|-- config/
|   `-- clinic_config.json
|
|-- logs/
|-- instance/
`-- venv/
```

## Installation and Setup

### 1. Clone or open the project

```bash
git clone <repository-url>
cd "Dental Clinic MS Flask"
```

If the project is already on your computer, open the project folder directly.

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

Windows PowerShell:

```powershell
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file based on `.env.example`.

Example:

```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=change-this-secret-key

DB_USER=root
DB_PASSWORD=1234
DB_HOST=127.0.0.1
DB_PORT=3308
DB_NAME=dental_clinic

LOG_FILE_NAME=clinic.log
```

`settings.py` reads these values from environment variables. If a value is missing, it uses the development defaults defined in that file.

### 6. Prepare the local clinic configuration

The application reads the log directory from:

```text
config/clinic_config.json
```

Example:

```json
{
  "log_directory": "logs"
}
```

-If this file does not exist, create it before running the app.

-This file is ignored by Git because it is local configuration.

-Create it manually by copying the example file:

-cp config/clinic_config.example.json config/clinic_config.json

-On Windows PowerShell:
 Copy-Item config/clinic_config.example.json config/clinic_config.json

### 7. Prepare the database

Make sure MySQL is running and the database exists.

Default database name:

```text
dental_clinic
```

Run the setup file if needed:

```bash
python setup.py
```

The app also calls `db.create_all()` on startup, so existing tables are reused and missing tables can be created automatically.

### 8. Run the application

```bash
python app.py
```

Open the app in your browser:

```text
http://127.0.0.1:5000
```

## Business Rules

### Appointments

- A scheduled appointment can be edited.
- A scheduled appointment can have treatments added, edited, or deleted.
- Only the session workflow should mark an appointment as done.
- A done appointment is treated as a medical record.
- A done appointment should not allow treatment changes.
- A done appointment should not be deleted.

### Treatments

- Treatments belong to appointments.
- Treatments can only be changed while the appointment is still scheduled.
- After ending the session, treatments become read-only.
- Treatment prices are predefined by procedure type.

### Payments

- Payments are added at the patient level.
- Payments are allocated to outstanding invoices.
- Payment allocation is handled by `services/payment_service.py`.
- Payments may still be added after an appointment is done.
- Overpayments may appear as patient credit.

### Invoices

- Invoices are based on appointment treatments.
- Invoice status depends on total cost, paid amount, and remaining amount.
- Invoice detail pages show treatments, costs, payments, and remaining balance.

## Route Organization

The application routes are split into Flask Blueprints:

```text
routes/dashboard.py      Dashboard and home page
routes/patients.py       Patient management and patient details
routes/appointments.py   Appointment list, add, edit, view, and delete
routes/treatments.py     Appointment sessions and treatment actions
routes/payments.py       Payments list and add payment
routes/invoices.py       Invoices list and invoice detail
```

`app.py` is responsible for:

- Creating the Flask app.
- Loading configuration.
- Initializing the database.
- Setting up logging.
- Registering Blueprints.
- Registering error handlers.
- Running the application.

## Ignored Files

The following files and folders should not be pushed to GitHub:

```text
venv/
.venv/
env/
__pycache__/
instance/
logs/
*.log
.env
.flaskenv
*.db
*.sqlite
*.sqlite3
*.zip
config/clinic_config.json
```

`config/clinic_config.json` contains local configuration. For sharing or deployment, add a sample file later, such as:

```text
config/clinic_config.example.json
```

## Development Notes

Completed cleanup:

- Added project documentation and dependency files.
- Moved configuration values into `settings.py`.
- Moved logging setup into `utils/logging_config.py`.
- Moved constants into `utils/constants.py`.
- Moved validation helpers into `utils/validators.py`.
- Moved payment allocation logic into `services/payment_service.py`.
- Split routes into Flask Blueprints.
- Organized templates into feature-based folders.
- Added dynamic appointment table updates.
- Moved old or unused templates into `templates/unused/`.

Future cleanup ideas:

- Review and remove old unused templates after final confirmation.
- Improve placeholder links such as Reports and Settings.
- Prepare the project for final export or submission.
