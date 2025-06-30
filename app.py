import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
from app import create_app
from dotenv import load_dotenv
from flask import render_template, request, flash, redirect, url_for, session, g
import random
import string

load_dotenv()
app = create_app()

def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# Optional: /info route for environment and Gunicorn check
@app.route('/info')
def info():
    env = os.getenv('FLASK_ENV', 'production')
    gunicorn = 'gunicorn' in os.environ.get('SERVER_SOFTWARE', '').lower()
    return {
        'environment': env,
        'using_gunicorn': gunicorn
    }

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    success = False
    if request.method == 'POST':
        email = request.form.get('email')
        message = request.form.get('message')
        # Here you could send an email or store the message
        success = True
    return render_template('contact.html', success=success)

@app.route('/referral/<code>')
def referral_signup(code):
    session['referred_by'] = code
    return redirect(url_for('auth.register'))

@app.route('/ads')
def ads():
    return render_template('ads.html')

@app.before_request
def set_referral():
    g.referred_by = session.get('referred_by')

# In registration logic (pseudo):
# if g.referred_by:
#     user.referred_by = g.referred_by
#     referrer = User.query.filter_by(referral_code=g.referred_by).first()
#     if referrer:
#         referrer.referral_credits += 1
#         db.session.commit()
#     user.referral_code = generate_referral_code()
# else:
#     user.referral_code = generate_referral_code()

if __name__ == "__main__":
    app = create_app()
    # Enable HTTPS for local development if cert.pem and key.pem exist
    cert_file = os.path.join(os.path.dirname(__file__), 'cert.pem')
    key_file = os.path.join(os.path.dirname(__file__), 'key.pem')
    new_port = 5599  # Changed port to 5599 as requested
    if os.path.exists(cert_file) and os.path.exists(key_file):
        app.run(host="0.0.0.0", port=new_port, ssl_context=(cert_file, key_file))
    else:
        app.run(host="0.0.0.0", port=new_port)
