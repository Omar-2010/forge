from flask import Blueprint, redirect, request
import requests

paymob_bp = Blueprint('paymob', __name__)

API_KEY = "ZXlKaGJHY2lPaUpJVXpVeE1pSXNJblI1Y0NJNklrcFhWQ0o5LmV5SmpiR0Z6Y3lJNklrMWxjbU5vWVc1MElpd2ljSEp2Wm1sc1pWOXdheUk2TVRBMU5qVTVNeXdpYm1GdFpTSTZJbWx1YVhScFlXd2lmUS5yVktiREd5VGJCSTJscDRoNTJWOWFQWTg3MmYtN0xMMy1MRVRDVEtqUEtuSHM0NVdHSUM2em1LNHAwQ3hkMzRpSnFnYmpwNlE0dEVPNGpQdE1pbEI4UQ=="
INTEGRATION_ID = 5169712
IFRAME_ID = 935733
YOUR_DOMAIN = "http://localhost:5000"  # Change this in production

@paymob_bp.route('/pay')
def pay():
    auth_res = requests.post("https://accept.paymob.com/api/auth/tokens", json={"api_key": API_KEY})
    auth_json = auth_res.json()
    if 'token' not in auth_json:
        return f'<h2>Paymob Auth Error: {auth_json.get("detail", auth_json)}</h2>'
    token = auth_json['token']
    order_res = requests.post("https://accept.paymob.com/api/ecommerce/orders", json={
        "auth_token": token,
        "delivery_needed": False,
        "amount_cents": "10000",
        "currency": "EGP",
        "items": []
    })
    order_id = order_res.json()['id']
    payment_res = requests.post("https://accept.paymob.com/api/acceptance/payment_keys", json={
        "auth_token": token,
        "amount_cents": "10000",
        "expiration": 3600,
        "order_id": order_id,
        "billing_data": {
            "apartment": "123",
            "email": "test@example.com",
            "floor": "1",
            "first_name": "Omar",
            "street": "Tahrir",
            "building": "10",
            "phone_number": "+201000000000",
            "shipping_method": "PKG",
            "postal_code": "12345",
            "city": "Cairo",
            "country": "EG",
            "last_name": "Mohamed",
            "state": "Cairo"
        },
        "currency": "EGP",
        "integration_id": INTEGRATION_ID
    })
    payment_token = payment_res.json()['token']
    iframe_url = f"https://accept.paymob.com/api/acceptance/iframes/{IFRAME_ID}?payment_token={payment_token}"
    return redirect(iframe_url)

@paymob_bp.route('/pay/<plan>')
def pay_plan(plan):
    # Plan mapping: price in EGP cents
    plans = {
        '1m': {'amount': 24000, 'desc': 'Pro 1 Month'},
        '3m': {'amount': 48000, 'desc': 'Pro 3 Months'},
        '6m': {'amount': 120000, 'desc': 'Pro 6 Months'},
        '1y': {'amount': 192000, 'desc': 'Pro 1 Year'},
    }
    if plan not in plans:
        return '<h2>Invalid plan selected.</h2>'
    auth_res = requests.post("https://accept.paymob.com/api/auth/tokens", json={"api_key": API_KEY})
    auth_json = auth_res.json()
    if 'token' not in auth_json:
        return f'<h2>Paymob Auth Error: {auth_json.get("detail", auth_json)}</h2>'
    token = auth_json['token']
    order_res = requests.post("https://accept.paymob.com/api/ecommerce/orders", json={
        "auth_token": token,
        "delivery_needed": False,
        "amount_cents": str(plans[plan]['amount']),
        "currency": "EGP",
        "items": []
    })
    order_id = order_res.json()['id']
    payment_res = requests.post("https://accept.paymob.com/api/acceptance/payment_keys", json={
        "auth_token": token,
        "amount_cents": str(plans[plan]['amount']),
        "expiration": 3600,
        "order_id": order_id,
        "billing_data": {
            "apartment": "123",
            "email": "test@example.com",
            "floor": "1",
            "first_name": "Omar",
            "street": "Tahrir",
            "building": "10",
            "phone_number": "+201000000000",
            "shipping_method": "PKG",
            "postal_code": "12345",
            "city": "Cairo",
            "country": "EG",
            "last_name": "Mohamed",
            "state": "Cairo"
        },
        "currency": "EGP",
        "integration_id": INTEGRATION_ID
    })
    payment_token = payment_res.json()['token']
    iframe_url = f"https://accept.paymob.com/api/acceptance/iframes/{IFRAME_ID}?payment_token={payment_token}"
    return redirect(iframe_url)

@paymob_bp.route('/success')
def success():
    # Activate the user's premium plan in the database
    from flask_login import current_user
    from app.models import Payment, User
    from app import db
    if not current_user.is_authenticated:
        return '<h2>Payment Successful! Please log in to activate your premium profile.</h2>'
    user = User.query.get(current_user.id)
    if user:
        user.plan = 'pro'
        from datetime import datetime, timedelta
        # Find the latest paid payment for this user
        payment = Payment.query.filter_by(user_id=user.id, status='paid').order_by(Payment.timestamp.desc()).first()
        if payment:
            # Set expiry based on duration
            user.pro_expiry = datetime.utcnow() + timedelta(days=30*payment.duration_months)
        db.session.commit()
        return '<h2>✅ Payment Successful! Your premium profile is now active.</h2>'
    return '<h2>Payment processed, but user not found.</h2>'
