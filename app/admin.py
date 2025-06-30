from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import User, SignInLog, Transaction, Payment
from app.ad_models import Ad
from app import db
from sqlalchemy.orm import joinedload
from app.plan_models import Plan
from app.support_models import SupportRequest
from app.admin_audit import log_admin_action

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_panel():
    if not current_user.is_admin:
        return render_template('error.html', error_message='Access denied: Admins only.', error_details=None), 403
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20
    # User search/filter
    q = request.args.get('q', '').strip()
    user_query = User.query
    if q:
        user_query = user_query.filter((User.email.ilike(f'%{q}%')) | (User.name.ilike(f'%{q}%')))
    users_paginated = user_query.options(joinedload(User.signins)).paginate(page=page, per_page=per_page, error_out=False)
    users = users_paginated.items
    user_signins = {u.id: u.signins[:5] for u in users}
    # Gather admin stats
    total_users = User.query.count()
    pro_users = User.query.filter_by(plan='pro').count()
    free_users = User.query.filter_by(plan='free').count()
    recent_signins = SignInLog.query.order_by(SignInLog.timestamp.desc()).limit(10).all()
    # Online users: last 10 minutes
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    online_cutoff = now - timedelta(minutes=10)
    online_users = User.query.join(SignInLog).filter(SignInLog.timestamp > online_cutoff).distinct().all()
    online_count = len(online_users)

    if request.method == 'POST':
        action = request.form.get('action')
        user_id = request.form.get('user_id')
        user = User.query.get(user_id)
        if action == 'delete' and user and not user.is_admin:
            db.session.delete(user)
            log_admin_action('delete_user', f'User ID: {user.id}, Email: {user.email}')
            flash('User deleted.', 'success')
        elif action == 'upgrade' and user and user.plan != 'pro':
            user.plan = 'pro'
            log_admin_action('upgrade_user', f'User ID: {user.id}, Email: {user.email}')
            flash('User upgraded to Pro.', 'success')
        elif action == 'downgrade' and user and user.plan != 'free':
            user.plan = 'free'
            log_admin_action('downgrade_user', f'User ID: {user.id}, Email: {user.email}')
            flash('User downgraded to Free.', 'success')
        elif action == 'make_admin' and user:
            user.is_admin = True
            log_admin_action('make_admin', f'User ID: {user.id}, Email: {user.email}')
            flash('User promoted to admin.', 'success')
        elif action == 'remove_admin' and user:
            user.is_admin = False
            log_admin_action('remove_admin', f'User ID: {user.id}, Email: {user.email}')
            flash('Admin rights removed from user.', 'success')
        elif action == 'edit' and user:
            new_name = request.form.get('new_name')
            new_plan = request.form.get('new_plan')
            if new_name:
                user.name = new_name
            if new_plan in ['free', 'pro']:
                user.plan = new_plan
            log_admin_action('edit_user', f'User ID: {user.id}, Email: {user.email}')
            flash('User info updated.', 'success')
        db.session.commit()
        return redirect(url_for('admin.admin_panel', page=page))
    return render_template('admin_dashboard.html', users=users, user_signins=user_signins, total_users=total_users, pro_users=pro_users, free_users=free_users, recent_signins=recent_signins, online_count=online_count, users_paginated=users_paginated)

@admin_bp.route('/admin/manage', methods=['GET'])
@login_required
def admin_manage():
    if not current_user.is_admin:
        return render_template('error.html', error_message='Access denied: Admins only.', error_details=None), 403
    users = User.query.all()
    # Add more management data as needed (e.g., pricing, payments)
    return render_template('admin_manage.html', users=users)

@admin_bp.route('/admin/subscriptions', methods=['GET', 'POST'])
@login_required
def admin_subscriptions():
    if not current_user.is_admin:
        return render_template('error.html', error_message='Access denied: Admins only.', error_details=None), 403
    q = request.args.get('q', '').strip()
    users = User.query
    if q:
        users = users.filter((User.email.ilike(f'%{q}%')) | (User.plan.ilike(f'%{q}%')))
    users = users.all()
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        new_plan = request.form.get('new_plan')
        user = User.query.get(user_id)
        if user and new_plan in ['free', 'pro']:
            user.set_plan(new_plan)
            flash(f"User {user.email}'s plan changed to {new_plan}.", 'success')
        db.session.commit()
        return redirect(url_for('admin.admin_subscriptions'))
    return render_template('admin_subscriptions.html', users=users)

@admin_bp.route('/admin/insights')
@login_required
def admin_insights():
    if not current_user.is_admin:
        return render_template('error.html', error_message='Access denied: Admins only.', error_details=None), 403
    from datetime import datetime, timedelta
    from app.models import VisitLog
    now = datetime.utcnow()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    year_ago = now - timedelta(days=365)
    visits_today = VisitLog.query.filter(VisitLog.timestamp >= today).count()
    visits_week = VisitLog.query.filter(VisitLog.timestamp >= week_ago).count()
    visits_month = VisitLog.query.filter(VisitLog.timestamp >= month_ago).count()
    visits_year = VisitLog.query.filter(VisitLog.timestamp >= year_ago).count()
    total_users = User.query.count()
    pro_users = User.query.filter_by(plan='pro').count()
    free_users = User.query.filter_by(plan='free').count()
    return render_template('admin_insights.html', visits_today=visits_today, visits_week=visits_week, visits_month=visits_month, visits_year=visits_year, total_users=total_users, pro_users=pro_users, free_users=free_users)

@admin_bp.route('/admin/finance', methods=['GET', 'POST'])
@login_required
def admin_finance():
    if not current_user.is_admin:
        return render_template('error.html', error_message='Access denied: Admins only.', error_details=None), 403
    from datetime import datetime
    q = request.args.get('q', '').strip()
    start = request.args.get('start')
    end = request.args.get('end')
    query = Transaction.query
    if q:
        query = query.filter(Transaction.description.ilike(f'%{q}%'))
    if start:
        query = query.filter(Transaction.date >= start)
    if end:
        query = query.filter(Transaction.date <= end)
    transactions = query.order_by(Transaction.date.desc()).all()
    # Add expense
    if request.method == 'POST' and 'add_expense' in request.form:
        amount = float(request.form['amount'])
        date = request.form['date']
        description = request.form['description']
        t = Transaction(type='expense', amount=amount, date=date, description=description)
        db.session.add(t)
        db.session.commit()
        flash('Expense added.', 'success')
        return redirect(url_for('admin.admin_finance'))
    # Delete expense
    if request.method == 'POST' and 'delete_expense' in request.form:
        tid = request.form['delete_id']
        t = Transaction.query.get(tid)
        if t and t.type == 'expense':
            db.session.delete(t)
            db.session.commit()
            flash('Expense deleted.', 'success')
        return redirect(url_for('admin.admin_finance'))
    # Calculate totals
    total_income = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type=='income').scalar() or 0
    total_expense = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.type=='expense').scalar() or 0
    net_profit = total_income - total_expense
    return render_template('admin_finance.html', transactions=transactions, total_income=total_income, total_expense=total_expense, net_profit=net_profit)

@admin_bp.route('/admin/export_users')
@login_required
def export_users():
    if not current_user.is_admin:
        return render_template('error.html', error_message='Access denied: Admins only.', error_details=None), 403
    import csv
    from io import StringIO
    users = User.query.all()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Email', 'Name', 'Plan', 'Is Admin', 'Created At', 'Last Used'])
    for u in users:
        cw.writerow([u.id, u.email, u.name, u.plan, u.is_admin, u.created_at, u.last_used])
    output = si.getvalue()
    from flask import Response
    return Response(output, mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=users.csv"})

@admin_bp.route('/admin/audit_log')
@login_required
def audit_log():
    if not current_user.is_admin:
        return render_template('error.html', error_message='Access denied: Admins only.', error_details=None), 403
    from app.admin_audit import AdminAuditLog
    page = request.args.get('page', 1, type=int)
    per_page = 25
    logs = AdminAuditLog.query.order_by(AdminAuditLog.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('admin_audit_log.html', logs=logs)

@admin_bp.route('/admin/analytics')
@login_required
def admin_analytics():
    if not current_user.is_admin:
        return render_template('error.html', error_message='Access denied: Admins only.', error_details=None), 403
    from app.models import VisitLog, Transaction
    from datetime import datetime, timedelta
    import calendar
    # User growth (last 12 months)
    now = datetime.utcnow()
    user_growth_labels = []
    user_growth_counts = []
    for i in range(11, -1, -1):
        month = (now.month - i - 1) % 12 + 1
        year = now.year if now.month - i > 0 else now.year - 1
        label = f"{calendar.month_abbr[month]} {year}"
        user_growth_labels.append(label)
        count = User.query.filter(User.created_at < datetime(year, month, 28)).count()
        user_growth_counts.append(count)
    user_growth_data = {"labels": user_growth_labels, "datasets": [{"label": "Users", "data": user_growth_counts, "borderColor": "#36a2eb", "fill": False}]}
    # Conversion stats (last 12 months)
    conversion_labels = user_growth_labels
    conversion_counts = []
    for i in range(11, -1, -1):
        month = (now.month - i - 1) % 12 + 1
        year = now.year if now.month - i > 0 else now.year - 1
        start = datetime(year, month, 1)
        end = datetime(year, month, 28)
        count = VisitLog.query.filter(VisitLog.timestamp >= start, VisitLog.timestamp < end).count()
        conversion_counts.append(count)
    conversion_data = {"labels": conversion_labels, "datasets": [{"label": "Conversions", "data": conversion_counts, "backgroundColor": "#4bc0c0"}]}
    # Plan pie chart
    pro_count = User.query.filter_by(plan='pro').count()
    free_count = User.query.filter_by(plan='free').count()
    plan_pie_data = {"labels": ["Pro", "Free"], "datasets": [{"data": [pro_count, free_count], "backgroundColor": ["#36a2eb", "#ff6384"]}]}
    # Revenue (last 12 months)
    revenue_labels = user_growth_labels
    revenue_amounts = []
    periods = [
        ('Last Month', 30),
        ('2 Months Ago', 60),
        ('3 Months Ago', 90),
        ('4 Months Ago', 120),
        ('5 Months Ago', 150),
        ('6 Months Ago', 180),
        ('7 Months Ago', 210),
        ('8 Months Ago', 240),
        ('9 Months Ago', 270),
        ('10 Months Ago', 300),
        ('11 Months Ago', 330),
        ('12 Months Ago', 365),
    ]
    for i, (label, days) in enumerate(periods):
        start = now - timedelta(days=days)
        end = now if i == 0 else now - timedelta(days=periods[i-1][1])
        # Use Transaction.date instead of Transaction.timestamp
        total = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.date >= start, Transaction.date < end).scalar() or 0
        revenue_amounts.append(float(total))
    revenue_data = {"labels": revenue_labels, "datasets": [{"label": "Revenue (EGP)", "data": revenue_amounts, "borderColor": "#ff6384", "fill": False}]}
    return render_template('admin_analytics.html', user_growth_data=user_growth_data, conversion_data=conversion_data, plan_pie_data=plan_pie_data, revenue_data=revenue_data)

@admin_bp.route('/admin/pricing', methods=['GET', 'POST'])
@login_required
def admin_pricing():
    if not current_user.is_admin:
        return render_template('error.html', error_message='Access denied: Admins only.', error_details=None), 403
    # Discount logic
    from app import db
    discount = db.session.execute(db.text('SELECT value FROM settings WHERE key="discount"')).scalar() if db.engine.dialect.has_table(db.engine, 'settings') else None
    discount_active = db.session.execute(db.text('SELECT value FROM settings WHERE key="discount_active"')).scalar() if db.engine.dialect.has_table(db.engine, 'settings') else None
    if request.method == 'POST':
        # Update or add plans
        for key in request.form:
            if key.startswith('price_'):
                plan_id = key.split('_')[1]
                plan = Plan.query.get(plan_id)
                if plan:
                    plan.price = float(request.form.get(f'price_{plan_id}'))
                    plan.description = request.form.get(f'desc_{plan_id}')
                    plan.duration_months = int(request.form.get(f'duration_{plan_id}'))
                    log_admin_action('edit_plan', f'Plan ID: {plan.id}, Name: {plan.name}')
            if key.startswith('delete_'):
                plan_id = key.split('_')[1]
                plan = Plan.query.get(plan_id)
                if plan:
                    log_admin_action('delete_plan', f'Plan ID: {plan.id}, Name: {plan.name}')
                    db.session.delete(plan)
        # Add new plan
        if request.form.get('new_name'):
            new_plan = Plan(
                name=request.form.get('new_name'),
                price=float(request.form.get('new_price')),
                description=request.form.get('new_desc'),
                duration_months=int(request.form.get('new_duration'))
            )
            db.session.add(new_plan)
            log_admin_action('add_plan', f'Plan Name: {new_plan.name}')
        # Discount update
        if 'discount_value' in request.form:
            value = float(request.form.get('discount_value', 0))
            db.session.execute(db.text('INSERT OR REPLACE INTO settings (key, value) VALUES ("discount", :value)'), {'value': value})
            log_admin_action('update_discount', f'Discount set to {value}%')
        if 'discount_active' in request.form:
            db.session.execute(db.text('INSERT OR REPLACE INTO settings (key, value) VALUES ("discount_active", :value)'), {'value': '1'})
            log_admin_action('activate_discount')
        else:
            db.session.execute(db.text('INSERT OR REPLACE INTO settings (key, value) VALUES ("discount_active", :value)'), {'value': '0'})
            log_admin_action('deactivate_discount')
        db.session.commit()
        flash('Pricing and discounts updated.', 'success')
        return redirect(url_for('admin.admin_pricing'))
    plans = Plan.query.order_by(Plan.duration_months).all()
    return render_template('admin_pricing.html', plans=plans, discount=discount, discount_active=discount_active)

@admin_bp.route('/admin/payments')
@login_required
def admin_payments():
    if not current_user.is_admin:
        return render_template('error.html', error_message='Access denied: Admins only.', error_details=None), 403
    from app.models import Payment, User
    page = request.args.get('page', 1, type=int)
    per_page = 25
    q = request.args.get('q', '').strip()
    query = Payment.query
    if q:
        query = query.filter((Payment.plan.ilike(f'%{q}%')) | (Payment.status.ilike(f'%{q}%')))
    payments = query.order_by(Payment.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('admin_payments.html', payments=payments)

@admin_bp.route('/admin/ads', methods=['GET', 'POST'])
@login_required
def admin_ads():
    if not current_user.is_admin:
        return render_template('error.html', error_message='Access denied: Admins only.', error_details=None), 403
    page = request.args.get('page', 1, type=int)
    per_page = 20
    q = request.args.get('q', '').strip()
    query = Ad.query
    if q:
        query = query.filter(Ad.name.ilike(f'%{q}%'))
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            name = request.form.get('name')
            code = request.form.get('code')
            position = request.form.get('position', 'main')
            ad = Ad(name=name, code=code, position=position)
            db.session.add(ad)
            db.session.commit()
            log_admin_action('add_ad', f'Ad Name: {ad.name}')
            flash('Ad created successfully.', 'success')
        elif action == 'edit':
            ad_id = request.form.get('ad_id')
            ad = Ad.query.get(ad_id)
            if ad:
                ad.name = request.form.get('name')
                ad.code = request.form.get('code')
                ad.position = request.form.get('position', 'main')
                ad.active = 'active' in request.form
                db.session.commit()
                log_admin_action('edit_ad', f'Ad ID: {ad.id}, Name: {ad.name}')
                flash('Ad updated.', 'success')
        elif action == 'delete':
            ad_id = request.form.get('ad_id')
            ad = Ad.query.get(ad_id)
            if ad:
                log_admin_action('delete_ad', f'Ad ID: {ad.id}, Name: {ad.name}')
                db.session.delete(ad)
                db.session.commit()
                flash('Ad deleted.', 'success')
        return redirect(url_for('admin.admin_ads'))
    ads = query.order_by(Ad.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('admin_ads.html', ads=ads)

@admin_bp.route('/admin/force-upgrade', methods=['POST'])
@login_required
def force_upgrade():
    if not current_user.is_admin:
        return render_template('error.html', error_message='Access denied: Admins only.', error_details=None), 403
    email = request.form.get('user_email')
    months = int(request.form.get('months') or 1)
    from datetime import datetime, timedelta
    user = User.query.filter_by(email=email).first()
    if user:
        user.plan = 'pro'
        user.pro_expiry = datetime.utcnow() + timedelta(days=30*months)
        db.session.commit()
        flash(f'User {email} upgraded to Pro for {months} month(s).', 'success')
    else:
        flash(f'User with email {email} not found.', 'danger')
    return redirect(url_for('admin.admin_manage'))

@admin_bp.route('/admin/support', methods=['GET', 'POST'])
@login_required
def admin_support():
    if not current_user.is_admin:
        return render_template('error.html', error_message='Access denied: Admins only.', error_details=None), 403
    from app.support_models import SupportRequest
    if request.method == 'POST':
        req_id = request.form.get('req_id')
        reply = request.form.get('reply')
        if req_id and reply:
            req = SupportRequest.query.get(req_id)
            if req:
                req.status = 'closed'
                req.read = True
                # Here you could send an email to the user with the reply (implement as needed)
                req.admin_reply = reply  # Add this field to the model if not present
                db.session.commit()
                flash('Reply sent and request closed.', 'success')
    requests = SupportRequest.query.order_by(SupportRequest.created_at.desc()).all()
    return render_template('admin_support.html', requests=requests)

@admin_bp.route('/admin/messages')
@login_required
def admin_messages():
    if not current_user.is_admin:
        return render_template('error.html', error_message='Access denied: Admins only.', error_details=None), 403
    from app.support_models import SupportRequest
    requests = SupportRequest.query.order_by(SupportRequest.created_at.desc()).all()
    return render_template('admin_support.html', requests=requests)

@admin_bp.route('/support/submit', methods=['POST'])
def submit_support():
    from flask import request, redirect, url_for, flash
    user_email = request.form.get('user_email')
    subject = request.form.get('subject')
    message = request.form.get('message')
    if not user_email or not subject or not message:
        flash('All fields are required.', 'danger')
        return redirect(request.referrer or '/')
    req = SupportRequest(user_email=user_email, subject=subject, message=message)
    db.session.add(req)
    db.session.commit()
    flash('Your support request has been submitted. Our team will contact you soon.', 'success')
    return redirect(request.referrer or '/')

@admin_bp.route('/admin/support/read/<int:req_id>', methods=['POST'])
@login_required
def mark_support_read(req_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admins only'}), 403
    req = SupportRequest.query.get_or_404(req_id)
    req.read = True
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/admin/support/unread/<int:req_id>', methods=['POST'])
@login_required
def mark_support_unread(req_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admins only'}), 403
    req = SupportRequest.query.get_or_404(req_id)
    req.read = False
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/admin/user/<int:user_id>/edit', methods=['POST'])
@login_required
def admin_edit_user(user_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admins only'}), 403
    user = User.query.get_or_404(user_id)
    email = request.form.get('email')
    name = request.form.get('name')
    new_password = request.form.get('new_password')
    if email and email != user.email:
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'error': 'Email already in use'}), 400
        user.email = email
    if name:
        user.name = name
    if new_password:
        from app import bcrypt
        user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/admin/user/<int:user_id>/deactivate', methods=['POST'])
@login_required
def admin_deactivate_user(user_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admins only'}), 403
    user = User.query.get_or_404(user_id)
    user.plan = 'deactivated'
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/admin/user/<int:user_id>/reset-password', methods=['POST'])
@login_required
def admin_reset_user_password(user_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admins only'}), 403
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password')
    if not new_password:
        return jsonify({'success': False, 'error': 'No password provided'}), 400
    from app import bcrypt
    user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/admin/user-manage')
@login_required
def admin_user_manage():
    if not current_user.is_admin:
        return render_template('error.html', error_message='Access denied: Admins only.', error_details=None), 403
    users = User.query.all()
    return render_template('admin_user_manage.html', users=users)
