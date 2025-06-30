from flask_login import login_required, current_user
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from .models import Payment, User
from . import db

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/pricing')
def pricing():
    return render_template('pricing.html')

@payments_bp.route('/billing', methods=['GET'])
@login_required
def billing():
    # Show all payments and subscription status for the current user
    payments = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.timestamp.desc()).all()
    return render_template('billing.html', payments=payments, user=current_user)

@payments_bp.route('/downgrade', methods=['POST'])
@login_required
def downgrade():
    user = User.query.get(current_user.id)
    user.plan = 'free'
    db.session.commit()
    flash('You have been downgraded to the Free plan.', 'success')
    return redirect(url_for('payments.billing'))

@payments_bp.route('/payments')
@login_required
def payments():
    # Show all payments for the current user
    payments = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.timestamp.desc()).all()
    return render_template('payments.html', payments=payments, user=current_user)
