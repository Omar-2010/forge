from app import db
from datetime import datetime

class SupportRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(32), default='open')  # open, closed, pending
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)  # New: track if admin has read the message
    admin_reply = db.Column(db.Text, nullable=True)  # Admin reply to the support request

    def __repr__(self):
        return f'<SupportRequest {self.user_email} - {self.subject}>'
