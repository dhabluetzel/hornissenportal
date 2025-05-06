import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
import os
from dotenv import load_dotenv

load_dotenv()

# Initialisierung der Erweiterungen
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
mail = Mail()

def create_app():
    app = Flask(__name__)

    # Setzen des Log-Ordners
    if not os.path.exists('app/log'):
        os.makedirs('app/log')

    # Logging konfigurieren
    logging.basicConfig(
        filename='app/log/logs.log',
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    app.logger = logging.getLogger(__name__)

    # Konfiguration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])
    app.config['UPLOAD_FOLDER'] = os.path.join('app', 'static', 'uploads')

    # Erweiterungen initialisieren
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # Modelle importieren
    from app.models import User, Report

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprints registrieren
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    return app
