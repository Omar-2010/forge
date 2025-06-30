import os
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from flask_migrate import Migrate
from dotenv import load_dotenv
from flask_cors import CORS
from flask_dance.contrib.google import make_google_blueprint, google
import random
import string

# Load environment variables
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
mail = Mail()
migrate = Migrate()

ADMIN_EMAIL_NOTIFY = 'pdf.forge.2010@gmail.com'


def create_app(config_name=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///pdfforge.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))
    app.config['MAX_CONTENT_LENGTH'] = None  # Remove upload size limit

    # Google OAuth setup
    app.config['GOOGLE_OAUTH_CLIENT_ID'] = os.getenv('GOOGLE_OAUTH_CLIENT_ID', '')
    app.config['GOOGLE_OAUTH_CLIENT_SECRET'] = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', '')
    if not app.config['GOOGLE_OAUTH_CLIENT_ID'] or not app.config['GOOGLE_OAUTH_CLIENT_SECRET']:
        print("[ERROR] Google OAuth client_id or client_secret not set. Google login will not work.")
    google_bp = make_google_blueprint(
        client_id=app.config['GOOGLE_OAUTH_CLIENT_ID'],
        client_secret=app.config['GOOGLE_OAUTH_CLIENT_SECRET'],
        scope=[
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "openid"
        ],
        redirect_url="/google_login/authorized"
    )
    app.register_blueprint(google_bp, url_prefix="/login")

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # Remove login_manager.login_view to prevent forced login redirect for any route
    # login_manager.login_view = 'auth.login'
    # login_manager.login_message = 'Please log in to access this page.'
    # login_manager.login_message_category = 'warning'

    # Register blueprints
    from .auth import auth_bp
    from .main import main_bp
    from .convert import convert_bp
    from .dashboard import dashboard_bp
    from .payments import payments_bp
    from .admin import admin_bp
    from .paymob import paymob_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(convert_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(paymob_bp)

    # Create upload folder if not exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html', error_message='Page not found', error_details=str(e)), 404

    @app.errorhandler(Exception)
    def handle_exception(e):
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            return render_template('error.html', error_message=str(e), error_details=e.description), e.code
        import traceback
        error_details = traceback.format_exc()
        return render_template('error.html', error_message='An unexpected error occurred.', error_details=error_details), 500

    # --- ADMIN AUTO-CREATION BLOCK RESTORED AFTER MIGRATION ---
    from .models import User
    import sqlalchemy
    with app.app_context():
        # Only run admin creation if 'is_admin' column exists
        inspector = sqlalchemy.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]
        if 'is_admin' in columns:
            # Only check for admin if running the app directly (not during CLI/migrations)
            import sys
            if __name__ == "__main__" or (hasattr(sys, 'argv') and ("run" in sys.argv or "shell" in sys.argv)):
                try:
                    if not User.query.filter_by(is_admin=True).first():
                        admin_email = os.getenv('ADMIN_EMAIL', 'admin@pdfforge.com')
                        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
                        if not User.query.filter_by(email=admin_email).first():
                            hashed_pw = bcrypt.generate_password_hash(admin_password).decode('utf-8')
                            admin_user = User(email=admin_email, password_hash=hashed_pw, plan='pro', is_admin=True, name='Admin')
                            db.session.add(admin_user)
                            db.session.commit()
                            print(f"[INIT] Admin account created: {admin_email} (default password: {admin_password})")
                        else:
                            user = User.query.filter_by(email=admin_email).first()
                            user.is_admin = True
                            db.session.commit()
                            print(f"[INIT] Existing user {admin_email} promoted to admin.")
                except Exception as e:
                    # Log and ignore errors during migration
                    print(f"[INFO] Skipping admin check during migration: {e}")
    # --- END RESTORED BLOCK ---

    # Helper email functions (move to separate file for production)
    def send_welcome_email(user):
        pass  # No-op for now, implement as needed

    def send_admin_notify(subject, body):
        pass  # No-op for now, implement as needed

    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['REMEMBER_COOKIE_SECURE'] = True
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    # Force HTTPS in production
    @app.before_request
    def before_request():
        if not app.debug and not request.is_secure and not request.host.startswith('localhost'):
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)

    from .utils import generate_referral_code

    return app
