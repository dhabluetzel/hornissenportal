import os
import uuid
import logging
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from flask_mail import Message
from app.forms import LoginForm, RegisterForm, ReportForm
from app.models import User, Report
from app import db, mail
from app.utils import reverse_geocode
from flask import send_file
import pandas as pd
from fpdf import FPDF
from io import BytesIO

bp = Blueprint('main', __name__)
logger = logging.getLogger('app')

# Startseite
@bp.route('/')
def home():
    logger.info("Home-Route aufgerufen")
    return redirect(url_for('main.login'))

# Login
@bp.route('/login', methods=['GET', 'POST'])
def login():
    logger.info("Login-Route aufgerufen")
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            logger.info(f"Login erfolgreich für {form.email.data}")
            flash('Login erfolgreich!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            logger.warning(f"Login fehlgeschlagen für {form.email.data}")
            flash('Login fehlgeschlagen. Bitte überprüfe deine Zugangsdaten.', 'danger')
    return render_template('login.html', form=form)

# Logout
@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Du wurdest ausgeloggt.', 'info')
    return redirect(url_for('main.login'))

# Dashboard – Meldungen des Users
@bp.route('/dashboard')
@login_required
def dashboard():
    reports = Report.query.filter_by(user_id=current_user.id).order_by(Report.timestamp.desc()).all()
    return render_template('dashboard.html', reports=reports)

# Meldung bearbeiten
@bp.route('/edit_report/<int:report_id>', methods=['GET', 'POST'])
@login_required
def edit_report(report_id):
    report = Report.query.get_or_404(report_id)
    if report.user_id != current_user.id:
        flash('Keine Berechtigung!', 'danger')
        return redirect(url_for('main.dashboard'))

    form = ReportForm(obj=report)
    if form.validate_on_submit():
        report.latitude = form.latitude.data
        report.longitude = form.longitude.data
        report.bundesland = form.bundesland.data
        report.type = form.type.data
        report.description = form.description.data

        photo = request.files.get('photo')
        if photo:
            filename = f"{uuid.uuid4().hex}_{secure_filename(photo.filename)}"
            upload_path = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_path, exist_ok=True)
            photo.save(os.path.join(upload_path, filename))
            report.photo_filename = filename

        db.session.commit()

        # Mail an den User + BCC an das Team
        try:
            msg = Message(
                subject="Deine Meldung wurde aktualisiert",
                recipients=[current_user.email],
                bcc=["info@umsiedlungen.ch"],
                body=f"""Hallo {current_user.email},

deine Meldung wurde erfolgreich aktualisiert.

Neue Details zur Meldung:
- Typ: {report.type}
- Ort: {report.bundesland}
- Koordinaten: ({report.latitude}, {report.longitude})
- Beschreibung: {report.description or '-'}

Du kannst die Änderungen im Dashboard jederzeit einsehen:
{url_for('main.dashboard', _external=True)}

Freundlichst  
Imkerei Hablützel

📍 https://www.velutina-service.ch
"""
            )
            mail.send(msg)
        except Exception as e:
            current_app.logger.error(f"Fehler beim Senden der Update-Mail: {e}")

        flash('Meldung aktualisiert!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('edit_report.html', form=form, report=report)

# Meldung löschen
@bp.route('/delete_report/<int:report_id>', methods=['POST'])
@login_required
def delete_report(report_id):
    report = Report.query.get_or_404(report_id)
    if report.user_id != current_user.id:
        flash('Keine Berechtigung!', 'danger')
        return redirect(url_for('main.dashboard'))

    db.session.delete(report)
    db.session.commit()
    flash('Meldung erfolgreich gelöscht.', 'success')
    return redirect(url_for('main.dashboard'))

# Registrierung
@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Diese E-Mail-Adresse ist bereits registriert.', 'danger')
            return redirect(url_for('main.register'))

        user = User(email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        # ✅ Mail an den User + BCC an das Team
        try:
            msg = Message(
                subject="Dein Hornissenportal-Account wurde erfolgreich erstellt",
                recipients=[user.email],
                bcc=["info@umsiedlungen.ch"],
                body=f"""Hallo {user.email},

dein Benutzerkonto für das Hornissenportal wurde erfolgreich eingerichtet.

Du kannst dich ab sofort unter folgendem Link einloggen:
{url_for('main.login', _external=True)}

📌 Deine Angaben:
- E-Mail: {user.email}

Bitte bewahre diese E-Mail für deine Unterlagen auf.

Freundlichst  
Imkerei Hablützel

📍 https://www.velutina-service.ch
"""
            )
            mail.send(msg)
        except Exception as e:
            current_app.logger.error(f"Fehler beim Senden der Registrierungs-Mail: {e}")

        flash('Registrierung erfolgreich! Bitte logge dich jetzt ein.', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html', form=form)
# Neue Meldung
@bp.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    form = ReportForm()
    if request.method == 'POST' and form.validate_on_submit():
        latitude = form.latitude.data
        longitude = form.longitude.data
        bundesland = form.bundesland.data
        type = form.type.data
        description = form.description.data

        photo = request.files.get('photo')
        if photo:
            filename = f"{uuid.uuid4().hex}_{secure_filename(photo.filename)}"
            upload_path = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_path, exist_ok=True)
            photo.save(os.path.join(upload_path, filename))
        else:
            flash('Foto ist ein Pflichtfeld!', 'danger')
            return redirect(url_for('main.report'))

        new_report = Report(
            user_id=current_user.id,
            latitude=latitude,
            longitude=longitude,
            bundesland=bundesland,
            type=type,
            description=description,
            photo_filename=filename
        )

        try:
            db.session.add(new_report)
            db.session.commit()

            # Bestätigungsmail an den User + BCC an Team
            try:
                msg = Message(
                    subject="Deine Hornissen-Meldung wurde gespeichert",
                    recipients=[current_user.email],
                    bcc=["info@umsiedlungen.ch", "info@imkerei.wacker.nrw"],
                    body=f"""Hallo {current_user.email},

deine neue Meldung wurde erfolgreich gespeichert.

Details zur Meldung:
- Typ: {type}
- Ort: {bundesland}
- Koordinaten: ({latitude}, {longitude})
- Beschreibung: {description or '-'}

Du kannst deine Meldung jederzeit im Dashboard einsehen:
{url_for('main.dashboard', _external=True)}

Vielen Dank für deinen Beitrag zur Bekämpfung der asiatischen Hornisse!

Freundlichst  
Imkerei Hablützel

📍 https://www.velutina-service.ch
"""
                )
                mail.send(msg)
            except Exception as e:
                current_app.logger.error(f"Fehler beim Senden der Bestätigungsmail: {e}")

            flash('Meldung erfolgreich eingereicht!', 'success')
            return redirect(url_for('main.dashboard'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Fehler beim Speichern der Meldung: {str(e)}")
            flash('Fehler beim Speichern der Meldung: ' + str(e), 'danger')
            return redirect(url_for('main.report'))

    return render_template('report.html', form=form)

# Admin: Nutzerübersicht
@bp.route('/admin/users')
@login_required
def admin_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users)

# Admin: Passwort zurücksetzen
@bp.route('/admin/reset_password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        new_password = request.form['new_password']
        user.set_password(new_password)
        db.session.commit()
        flash('Passwort erfolgreich zurückgesetzt.', 'success')
        return redirect(url_for('main.admin_users'))

    return render_template('reset_password.html', user=user)

# Admin-Dashboard mit Filter
@bp.route('/admin', methods=['GET'])
@login_required
def admin_dashboard():
    selected_state = request.args.get('bundesland')

    if selected_state:
        reports = Report.query.filter_by(bundesland=selected_state).order_by(Report.timestamp.desc()).all()
    else:
        reports = Report.query.order_by(Report.timestamp.desc()).all()

    bundesländer = db.session.query(Report.bundesland).distinct().all()
    bundesländer = [b[0] for b in bundesländer]

    return render_template('admin_dashboard.html', reports=reports, bundesländer=bundesländer, selected_state=selected_state)

# Übersichtskarte
@bp.route('/map')
@login_required
def map_view():
    reports = Report.query.all()
    meldungen = [{
        'latitude': float(r.latitude),
        'longitude': float(r.longitude),
        'type': r.type,
        'description': r.description,
        'bundesland': r.bundesland,
        'photo_url': url_for('static', filename=f'uploads/{r.photo_filename}') if r.photo_filename else None
    } for r in reports]
    return render_template('map.html', meldungen=meldungen)
# Admin: Adminrechte vergeben
@bp.route('/admin/make_admin/<int:user_id>', methods=['POST'])
@login_required
def make_admin(user_id):
    if not current_user.is_admin:
        flash('Keine Berechtigung.', 'danger')
        current_app.logger.warning(f"Unauthorized attempt to make user {user_id} admin by {current_user.email}")
        return redirect(url_for('main.admin_users'))
    
    user = User.query.get_or_404(user_id)
    user.is_admin = True
    db.session.commit()
    flash(f'{user.email} ist jetzt Admin!', 'success')
    current_app.logger.info(f"Admin rights granted to {user.email}")
    return redirect(url_for('main.admin_users'))

# Admin: Adminrechte entziehen
@bp.route('/admin/remove_admin/<int:user_id>', methods=['POST'])
@login_required
def remove_admin(user_id):
    if not current_user.is_admin:
        flash('Keine Berechtigung.', 'danger')
        current_app.logger.warning(f"Unauthorized attempt to remove admin rights from user {user_id} by {current_user.email}")
        return redirect(url_for('main.admin_users'))
    
    user = User.query.get_or_404(user_id)
    user.is_admin = False
    db.session.commit()
    flash(f'Adminrechte von {user.email} wurden entfernt.', 'success')
    current_app.logger.info(f"Admin rights removed from {user.email}")
    return redirect(url_for('main.admin_users'))
@bp.route('/admin/export/excel')
@login_required
def export_excel():
    if not current_user.is_admin:
        flash("Keine Berechtigung.", "danger")
        return redirect(url_for('main.admin_dashboard'))

    reports = Report.query.all()
    data = [{
        'ID': r.id,
        'Typ': r.type,
        'Bundesland': r.bundesland,
        'Beschreibung': r.description,
        'Koordinaten': f"{r.latitude}, {r.longitude}",
        'Datum': r.timestamp.strftime('%Y-%m-%d %H:%M')
    } for r in reports]

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Meldungen')

    output.seek(0)
    return send_file(output, download_name='meldungen.xlsx', as_attachment=True)

@bp.route('/admin/export/pdf')
@login_required
def export_pdf():
    if not current_user.is_admin:
        flash("Keine Berechtigung.", "danger")
        return redirect(url_for('main.admin_dashboard'))

    reports = Report.query.all()
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Hornissen-Meldungen", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", size=12)

    for r in reports:
        pdf.cell(0, 10, f"ID: {r.id} | Typ: {r.type} | Ort: {r.bundesland}", ln=True)
        pdf.cell(0, 10, f"Koordinaten: {r.latitude}, {r.longitude}", ln=True)
        if r.description:
            pdf.multi_cell(0, 10, f"Beschreibung: {r.description}")
        pdf.cell(0, 10, "----------------------------", ln=True)

    # PDF als Bytes erzeugen
    pdf_output = pdf.output(dest='S').encode('latin-1')
    output_stream = BytesIO()
    output_stream.write(pdf_output)
    output_stream.seek(0)

    return send_file(output_stream, download_name='meldungen.pdf', as_attachment=True)
@bp.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Keine Berechtigung.', 'danger')
        return redirect(url_for('main.admin_users'))

    user = User.query.get_or_404(user_id)

    # User darf sich nicht selbst löschen
    if user.id == current_user.id:
        flash('Du kannst dich nicht selbst löschen.', 'warning')
        return redirect(url_for('main.admin_users'))

    try:
        # Reports behalten, aber user_id auf NULL setzen
        reports = Report.query.filter_by(user_id=user.id).all()
        for report in reports:
            report.user_id = None

        db.session.delete(user)
        db.session.commit()
        flash(f'Benutzer {user.email} wurde gelöscht. Meldungen bleiben erhalten.', 'success')
        current_app.logger.info(f"Benutzer {user.email} gelöscht, Meldungen beibehalten.")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Fehler beim Löschen von Benutzer {user.email}: {e}")
        flash('Fehler beim Löschen des Benutzers.', 'danger')

    return redirect(url_for('main.admin_users'))