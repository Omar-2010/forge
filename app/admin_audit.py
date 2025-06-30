from app import db
from flask_login import current_user
from datetime import datetime

class AdminAuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<AdminAuditLog {self.action} by {self.admin_id}>'

def log_admin_action(action, details=None):
    if current_user.is_authenticated and current_user.is_admin:
        log = AdminAuditLog(admin_id=current_user.id, action=action, details=details)
        db.session.add(log)
        db.session.commit()
