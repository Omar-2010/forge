from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import current_user
from app.models import VisitLog, db
from app.plan_models import Plan
from app.utils import get_active_ads  # <-- Import helper

main_bp = Blueprint('main', __name__)

@main_bp.before_app_request
def log_visit():
    if request.endpoint not in ['static']:
        visit = VisitLog(
            user_id=current_user.id if hasattr(current_user, 'id') and current_user.is_authenticated else None,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(visit)
        db.session.commit()

@main_bp.app_errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@main_bp.app_errorhandler(500)
def server_error(e):
    return render_template('error.html'), 500

@main_bp.route('/')
def index():
    ads = get_active_ads('main') if not (hasattr(current_user, 'is_admin') and current_user.is_admin) and (not hasattr(current_user, 'plan') or current_user.plan == 'free') else []
    return render_template('index.html', ads=ads)

@main_bp.route('/contact')
def contact():
    return render_template('contact.html')

@main_bp.route('/info')
def info():
    return render_template('info.html')

@main_bp.route('/pricing')
def pricing():
    # Fetch plans and discount from DB
    plans = Plan.query.order_by(Plan.duration_months).all()
    discount = db.session.execute(db.text('SELECT value FROM settings WHERE key="discount"')).scalar()
    discount_active = db.session.execute(db.text('SELECT value FROM settings WHERE key="discount_active"')).scalar()
    try:
        discount = float(discount) if discount else 0
    except Exception:
        discount = 0
    discount_active = str(discount_active) == '1'
    ads = get_active_ads('main') if not (hasattr(current_user, 'is_admin') and current_user.is_admin) and (not hasattr(current_user, 'plan') or current_user.plan == 'free') else []
    return render_template('pricing.html', plans=plans, discount=discount, discount_active=discount_active, ads=ads)
