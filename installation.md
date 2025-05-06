Installationsanleitung Hornissenportal
Installationsanleitung Hornissenportal

Voraussetzungen
•	Ubuntu 22.04 VPS
•	root-Zugriff
•	Plesk (für Domains & Mail)
•	Python 3.12
•	Virtuelle Umgebung
•	MySQL oder SQLite

1. System vorbereiten
apt update && apt upgrade -y
apt install python3.12 python3.12-venv python3-pip build-essential libssl-dev libffi-dev python3-dev libmysqlclient-dev -y

2. Virtuelle Umgebung erstellen
python3.12 -m venv venv
source venv/bin/activate

3. Projekt klonen
git clone https://github.com/dhabluetzel/velutina.git
cd velutina

4. Abhängigkeiten installieren
pip install -r requirements.txt

5. Umgebungsvariablen setzen (.env)
SECRET_KEY=dein-super-secret-key
DATABASE_URL=sqlite:///app.db  # oder mysql+pymysql://user:pass@host/db
MAIL_SERVER=serverXX.hostfactory.ch
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=deine@mail.ch
MAIL_PASSWORD=deinpasswort

6. Datenbank initialisieren
flask db init
flask db migrate
flask db upgrade

7. Start mit Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app

8. Nginx-Proxy konfigurieren
•	Weiterleitung von 443 auf 8000
•	SSL-Zertifikat konfigurieren

9. Systemd-Dienst (optional)
Erstelle z.B. `/etc/systemd/system/gunicorn-hornissenportal.service`.

10. Zugriff testen
•	https://scan.velutina-service.ch/
•	Registrierung & Upload testen
