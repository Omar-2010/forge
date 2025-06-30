from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

ADMIN_EMAILS = [
    'pdf.forge.2010@gmail.com',
]
ADMIN_PASSWORD = 'FUNpool@2010'

app = create_app()
with app.app_context():
    for email in ADMIN_EMAILS:
        user = User.query.filter_by(email=email).first()
        if user:
            user.password_hash = generate_password_hash(ADMIN_PASSWORD)
            user.set_admin(True)
            print(f'{email} promoted to admin and password set.')
        else:
            user = User(email=email, password_hash=generate_password_hash(ADMIN_PASSWORD), is_admin=True, plan='pro', name='PDF Forge Admin')
            db.session.add(user)
            db.session.commit()
            print(f'Admin user {email} created with fixed password.')
