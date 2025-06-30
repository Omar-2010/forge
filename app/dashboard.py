from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app import db, bcrypt
from app.utils import get_active_ads  # <-- Import helper

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    # Show user plan and admin status
    ads = get_active_ads('main') if not current_user.is_admin and current_user.plan == 'free' else []
    return render_template('dashboard.html', is_admin=current_user.is_admin, plan=current_user.plan, user=current_user, ads=ads)

@dashboard_bp.route('/profile')
@login_required
def profile():
    # Pass current_user as 'user' for template compatibility
    ads = get_active_ads('main') if not current_user.is_admin and current_user.plan == 'free' else []
    return render_template('profile.html', user=current_user, is_admin=current_user.is_admin, plan=current_user.plan, ads=ads)

@dashboard_bp.route('/profile/edit', methods=['POST'])
@login_required
def edit_profile():
    email = request.form.get('email')
    name = request.form.get('name')
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    # Check current password
    if not bcrypt.check_password_hash(current_user.password_hash, current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('profile'))
    # Check if email is changing and not taken
    if email != current_user.email:
        from app.models import User
        if User.query.filter_by(email=email).first():
            flash('Email already in use.', 'danger')
            return redirect(url_for('profile'))
        current_user.email = email
    current_user.name = name
    if new_password:
        current_user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()
    flash('Profile updated successfully.', 'success')
    return redirect(url_for('profile'))

@dashboard_bp.route('/activity')
@login_required
def user_activity():
    from app.models import SignInLog
    logs = SignInLog.query.filter_by(user_id=current_user.id).order_by(SignInLog.timestamp.desc()).limit(20).all()
    return render_template('user_activity.html', logs=logs)

@dashboard_bp.errorhandler(400)
def bad_request_error(error):
    return render_template('error.html', error_message='Bad Request', error_details=str(error)), 400

@dashboard_bp.errorhandler(401)
def unauthorized_error(error):
    return render_template('error.html', error_message='Unauthorized', error_details=str(error)), 401

@dashboard_bp.errorhandler(403)
def forbidden_error(error):
    return render_template('error.html', error_message='Forbidden', error_details=str(error)), 403

@dashboard_bp.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error_message='Page Not Found', error_details=str(error)), 404

@dashboard_bp.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error_message='Internal Server Error', error_details=str(error)), 500
