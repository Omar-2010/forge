from app import db
from datetime import datetime

class Ad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.Text, nullable=False)  # HTML/JS code for the ad
    active = db.Column(db.Boolean, default=True)
    position = db.Column(db.String(50), default='main')  # e.g., 'main', 'sidebar', 'footer'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Ad {self.name}>'
