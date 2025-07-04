# PDFForge

PDFForge is a full-featured iLovePDF.com clone web application built with Flask, Bootstrap, SQLAlchemy, Stripe, and Jinja2. It provides PDF and file tools, user authentication, and payment integration for a professional, production-ready experience.

## Features
- Convert, merge, split, compress, and manipulate PDF files
- User registration, login, and dashboard
- Stripe payments for Pro accounts
- Secure file handling and auto-deletion
- Admin panel for user and stats management
- Responsive Bootstrap frontend

## Setup Instructions

1. **Clone the repository**
2. **Create a virtual environment**
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate
   ```
3. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```
4. **Configure environment variables**
   - Copy `.env` and set your `SECRET_KEY`, `STRIPE_SECRET_KEY`, and `STRIPE_PUBLISHABLE_KEY`.
5. **Run the app locally**
   ```powershell
   flask db upgrade
   flask run
   ```

## Deployment
- Use `gunicorn` for production: `gunicorn wsgi:app`
- Deploy to Render or Heroku using `render.yaml` or `Procfile`

## Stripe Integration
- Set your Stripe keys in the `.env` file
- Free users: 3 conversions/day; Pro users: unlimited

## License
MIT License

---
For more details, see the documentation and code comments.
#   P D f - F O R G E - 2 0 1 0  
 #   f o r g e  
 