from . import db
from flask_login import UserMixin
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    plan = db.Column(db.String(20), default='free')
    conversion_count = db.Column(db.Integer, default=0)
    last_used = db.Column(db.Date, nullable=True)
    name = db.Column(db.String(100), nullable=True)
    # stripe_id = db.Column(db.String(255), nullable=True)  # Removed Stripe
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    referral_code = db.Column(db.String(20), unique=True, nullable=True)
    referred_by = db.Column(db.String(20), nullable=True)
    referral_credits = db.Column(db.Integer, default=0)
    pro_expiry = db.Column(db.DateTime, nullable=True)

    @property
    def is_pro(self):
        from datetime import datetime
        return self.plan == 'pro' and self.pro_expiry and self.pro_expiry > datetime.utcnow()

    @property
    def pro_expiry_days_left(self):
        from datetime import datetime
        if self.pro_expiry:
            delta = self.pro_expiry - datetime.utcnow()
            return max(delta.days, 0)
        return 0

    @property
    def referral_history(self):
        # Returns a list of users referred by this user
        return User.query.filter_by(referred_by=self.referral_code).all()

    def set_admin(self, value: bool):
        self.is_admin = value
        if value:
            self.plan = 'pro'  # Admin is always pro
        db.session.commit()

    def set_plan(self, plan: str):
        self.plan = plan
        db.session.commit()

    def delete_account(self):
        db.session.delete(self)
        db.session.commit()

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # stripe_id = db.Column(db.String(255), nullable=False)  # Removed Stripe
    status = db.Column(db.String(50), nullable=False)
    plan = db.Column(db.String(20), nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    filename = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    converted_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    plan = db.Column(db.String(20), nullable=True)  # e.g., 'pro', 'free'
    duration_months = db.Column(db.Integer, default=1)  # Number of months for the plan
    status = db.Column(db.String(32), default='paid')  # paid, pending, failed
    method = db.Column(db.String(32), nullable=True)  # e.g., 'stripe', 'paymob', 'manual'

    @property
    def is_recurring(self):
        return self.duration_months > 1

    @property
    def end_date(self):
        from datetime import timedelta
        return self.timestamp + timedelta(days=30*self.duration_months)

class SignInLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    method = db.Column(db.String(32), nullable=False)  # 'email' or 'google'
    user = db.relationship('User', backref=db.backref('signins', lazy=True))

class VisitLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(256), nullable=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Null for expenses
    type = db.Column(db.String(10), nullable=False)  # 'income' or 'expense'
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)
    description = db.Column(db.String(255), nullable=True)

    user = db.relationship('User', backref=db.backref('transactions', lazy=True))
