import random
import string
from app.models import User
from app.ad_models import Ad  # <-- Import Ad model

def generate_referral_code(length=8):
    """Generate a unique referral code."""
    while True:
        code = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        if not User.query.filter_by(referral_code=code).first():
            return code

def get_active_ads(position='main'):
    """Fetch all active ads for a given position (default: 'main')."""
    return Ad.query.filter_by(active=True, position=position).order_by(Ad.created_at.desc()).all()
