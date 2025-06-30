from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app, g
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, SignInLog
from . import db, bcrypt, login_manager, mail
from flask_dance.contrib.google import google
from app.utils import generate_referral_code
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            # Log sign-in
            signin = SignInLog(user_id=user.id, method='email')
            db.session.add(signin)
            db.session.commit()
            return redirect(url_for('main.index'))  # Redirect to home after login
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'warning')
            return redirect(url_for('auth.register'))
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        is_first_user = User.query.count() == 0
        user = User(name=name, email=email, password_hash=hashed_pw, is_admin=is_first_user)
        db.session.add(user)
        # Referral system
        from flask import g, session
        referred_by = session.get('referred_by') or getattr(g, 'referred_by', None)
        user.referral_code = generate_referral_code()
        if referred_by:
            user.referred_by = referred_by
            referrer = User.query.filter_by(referral_code=referred_by).first()
            if referrer:
                # Give referrer 1 month free (extend pro_expiry)
                now = datetime.utcnow()
                if referrer.pro_expiry and referrer.pro_expiry > now:
                    referrer.pro_expiry += timedelta(days=30)
                else:
                    referrer.pro_expiry = now + timedelta(days=30)
                referrer.plan = 'pro'
                referrer.referral_credits += 1
                # Give new user 1 week free (extend pro_expiry)
                user.pro_expiry = now + timedelta(days=7)
                user.plan = 'pro'
                db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/google_login/authorized')
def google_login_authorized():
    if not google.authorized:
        flash('Google login failed.', 'danger')
        return redirect(url_for('auth.login'))
    resp = google.get('/oauth2/v2/userinfo')
    if not resp.ok:
        flash('Failed to fetch user info from Google.', 'danger')
        return redirect(url_for('auth.login'))
    info = resp.json()
    email = info.get('email')
    name = info.get('name') or email.split('@')[0]
    user = User.query.filter_by(email=email).first()
    is_new = False
    if not user:
        user = User(name=name, email=email, password_hash='google', is_admin=False)
        db.session.add(user)
        db.session.commit()
        is_new = True
    login_user(user)
    signin = SignInLog(user_id=user.id, method='google')
    db.session.add(signin)
    db.session.commit()
    flash('Logged in with Google!', 'success')
    return redirect(url_for('main.index'))  # Redirect to home after Google login

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            flash('A password reset link would be sent to your email (feature disabled).', 'info')
        else:
            flash('No account found with that email.', 'danger')
    return render_template('reset_password.html')

@auth_bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    # Password reset token logic disabled (no email support)
    flash('Password reset via email is disabled.', 'danger')
    return redirect(url_for('auth.reset_password'))
