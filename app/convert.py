from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app, jsonify
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from .models import File
from . import db
from pdf2docx import Converter
from docx2pdf import convert as docx2pdf_convert
import img2pdf
import fitz  # PyMuPDF
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from PIL import Image
from flask_login import login_required, current_user
from sqlalchemy import func
from app.utils import get_active_ads  # <-- Import helper

convert_bp = Blueprint('convert', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'jpg', 'jpeg', 'png'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_output_filename(filename, suffix, ext=None):
    base, _ = os.path.splitext(filename)
    if ext:
        return f"{base}_{suffix}.{ext}"
    return f"{base}_{suffix}"


# Helper function to check free user conversion limit
def free_user_conversion_limit_reached(user):
    if not user.is_authenticated or user.plan != 'free':
        return False
    today = datetime.utcnow().date()
    count = File.query.filter(
        File.user_id == user.id,
        func.date(File.created_at) == today
    ).count()
    return count >= 10


@convert_bp.route('/convert/pdf-to-word', methods=['GET', 'POST'])
@login_required
def pdf_to_word():
    import logging
    logging.basicConfig(level=logging.DEBUG)
    if free_user_conversion_limit_reached(current_user):
        flash('Free users are limited to 10 conversions per day. Upgrade to Pro for unlimited conversions.', 'warning')
        return redirect(url_for('dashboard'))
    ads = get_active_ads('main') if current_user.plan == 'free' else []
    if request.method == 'POST':
        logging.debug(f"Request.files: {request.files}")
        if 'file' not in request.files:
            flash('No file part in the request.', 'danger')
            logging.error('No file part in the request.')
            return redirect(request.url)
        file = request.files['file']
        logging.debug(f"File received: {file.filename}")
        if file.filename == '':
            flash('No file selected.', 'danger')
            logging.error('No file selected.')
            return redirect(request.url)
        if file and allowed_file(file.filename) and file.filename.lower().endswith('.pdf'):
            filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_path)
            logging.info(f"File saved to: {upload_path}")
            output_filename = get_output_filename(filename, 'word', 'docx')
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)
            try:
                cv = Converter(upload_path)
                cv.convert(output_path, start=0, end=None)
                cv.close()
                flash('File converted successfully!', 'success')
                logging.info(f"File converted to: {output_path}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': True, 'filename': output_filename})
                return redirect(url_for('convert.result', filename=output_filename))
            except Exception as e:
                flash(f'Conversion error: {e}', 'danger')
                logging.error(f'Conversion error: {e}')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': False, 'error': str(e)}), 500
                return redirect(request.url)
        else:
            flash('Invalid file type. Please upload a PDF.', 'danger')
            logging.error('Invalid file type.')
    return render_template('convert.html', tool='PDF to Word', ads=ads)


@convert_bp.route('/convert/word-to-pdf', methods=['GET', 'POST'])
@login_required
def word_to_pdf():
    if free_user_conversion_limit_reached(current_user):
        flash('Free users are limited to 10 conversions per day. Upgrade to Pro for unlimited conversions.', 'warning')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        file = request.files.get('file')
        if file and allowed_file(file.filename) and file.filename.lower().endswith('.docx'):
            filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_path)
            output_filename = get_output_filename(filename, 'pdf', 'pdf')
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)
            docx2pdf_convert(upload_path, output_path)
            flash('File converted successfully!', 'success')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'filename': output_filename})
            return redirect(url_for('convert.result', filename=output_filename))
        flash('Invalid file type. Please upload a DOCX.', 'danger')
    return render_template('convert.html', tool='Word to PDF')


@convert_bp.route('/convert/jpg-to-pdf', methods=['GET', 'POST'])
@login_required
def jpg_to_pdf():
    import logging
    logging.basicConfig(level=logging.DEBUG)
    if free_user_conversion_limit_reached(current_user):
        flash('Free users are limited to 10 conversions per day. Upgrade to Pro for unlimited conversions.', 'warning')
        return redirect(url_for('dashboard'))
    ads = get_active_ads('main') if current_user.plan == 'free' else []
    if request.method == 'POST':
        logging.debug(f"Request.files: {request.files}")
        if 'file' not in request.files:
            flash('No file part in the request.', 'danger')
            logging.error('No file part in the request.')
            return redirect(request.url)
        file = request.files['file']
        logging.debug(f"File received: {file.filename}")
        if file.filename == '':
            flash('No file selected.', 'danger')
            logging.error('No file selected.')
            return redirect(request.url)
        if file and allowed_file(file.filename) and file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_path)
            logging.info(f"File saved to: {upload_path}")
            output_filename = get_output_filename(filename, 'pdf', 'pdf')
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)
            try:
                image = Image.open(upload_path)
                if image.mode in ("RGBA", "P"):
                    image = image.convert("RGB")
                image.save(output_path, "PDF", resolution=100.0)
                flash('File converted successfully!', 'success')
                logging.info(f"File converted to: {output_path}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': True, 'filename': output_filename})
                return redirect(url_for('convert.result', filename=output_filename))
            except Exception as e:
                flash(f'Error converting image: {e}', 'danger')
                logging.error(f'Error converting image: {e}')
                return redirect(request.url)
        else:
            flash('Invalid file type. Please upload a JPG, JPEG, or PNG.', 'danger')
            logging.error('Invalid file type.')
    return render_template('convert.html', tool='JPG to PDF', ads=ads)


@convert_bp.route('/convert/pdf-to-jpg', methods=['GET', 'POST'])
@login_required
def pdf_to_jpg():
    if free_user_conversion_limit_reached(current_user):
        flash('Free users are limited to 10 conversions per day. Upgrade to Pro for unlimited conversions.', 'warning')
        return redirect(url_for('dashboard'))
    ads = get_active_ads('main') if current_user.plan == 'free' else []
    if request.method == 'POST':
        file = request.files.get('file')
        if file and allowed_file(file.filename) and file.filename.lower().endswith('.pdf'):
            filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_path)
            output_files = []
            doc = fitz.open(upload_path)
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                pix = page.get_pixmap()
                output_filename = get_output_filename(filename, f'page{page_num+1}', 'jpg')
                output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)
                pix.save(output_path)
                output_files.append(output_filename)
            doc.close()
            flash('File converted successfully!', 'success')
            # For simplicity, show only the first page's image for download
            return redirect(url_for('convert.result', filename=output_files[0]))
        flash('Invalid file type. Please upload a PDF.', 'danger')
    return render_template('convert.html', tool='PDF to JPG', ads=ads)


@convert_bp.route('/merge-pdf', methods=['GET', 'POST'])
@login_required
def merge_pdf():
    if free_user_conversion_limit_reached(current_user):
        flash('Free users are limited to 10 conversions per day. Upgrade to Pro for unlimited conversions.', 'warning')
        return redirect(url_for('dashboard'))
    ads = get_active_ads('main') if current_user.plan == 'free' else []
    if request.method == 'POST':
        files = request.files.getlist('files')
        if files and all(f.filename for f in files):
            merger = PdfMerger()
            output_filename = get_output_filename('merged', 'pdf', 'pdf')
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)
            for file in files:
                if allowed_file(file.filename) and file.filename.lower().endswith('.pdf'):
                    filename = secure_filename(file.filename)
                    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(upload_path)
                    merger.append(upload_path)
                else:
                    flash('Invalid file type. Only PDFs allowed.', 'danger')
                    return redirect(request.url)
            merger.write(output_path)
            merger.close()
            flash('Files merged successfully!', 'success')
            return redirect(url_for('convert.result', filename=output_filename))
        flash('Please select valid PDF files.', 'danger')
    return render_template('convert.html', tool='Merge PDF', ads=ads)


@convert_bp.route('/split-pdf', methods=['GET', 'POST'])
@login_required
def split_pdf():
    if free_user_conversion_limit_reached(current_user):
        flash('Free users are limited to 10 conversions per day. Upgrade to Pro for unlimited conversions.', 'warning')
        return redirect(url_for('dashboard'))
    ads = get_active_ads('main') if current_user.plan == 'free' else []
    if request.method == 'POST':
        file = request.files.get('file')
        start_page = int(request.form.get('start_page', 1))
        end_page = int(request.form.get('end_page', 1))
        if file and allowed_file(file.filename) and file.filename.lower().endswith('.pdf'):
            filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_path)
            reader = PdfReader(upload_path)
            writer = PdfWriter()
            for i in range(start_page-1, end_page):
                writer.add_page(reader.pages[i])
            output_filename = get_output_filename(filename, f'split_{start_page}_{end_page}', 'pdf')
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)
            with open(output_path, 'wb') as f:
                writer.write(f)
            flash('File split successfully!', 'success')
            return redirect(url_for('convert.result', filename=output_filename))
        flash('Invalid file type or page range.', 'danger')
    return render_template('convert.html', tool='Split PDF', ads=ads)


@convert_bp.route('/compress-pdf', methods=['GET', 'POST'])
@login_required
def compress_pdf():
    if free_user_conversion_limit_reached(current_user):
        flash('Free users are limited to 10 conversions per day. Upgrade to Pro for unlimited conversions.', 'warning')
        return redirect(url_for('dashboard'))
    ads = get_active_ads('main') if current_user.plan == 'free' else []
    if request.method == 'POST':
        file = request.files.get('file')
        if file and allowed_file(file.filename) and file.filename.lower().endswith('.pdf'):
            filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_path)
            output_filename = get_output_filename(filename, 'compressed', 'pdf')
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename)
            # Simple compression: re-save with PyMuPDF
            doc = fitz.open(upload_path)
            doc.save(output_path, deflate=True)
            doc.close()
            flash('File compressed successfully!', 'success')
            return redirect(url_for('convert.result', filename=output_filename))
        flash('Invalid file type. Please upload a PDF.', 'danger')
    return render_template('convert.html', tool='Compress PDF', ads=ads)


@convert_bp.route('/result/<filename>')
def result(filename):
    ads = get_active_ads('main') if not current_user.is_authenticated or current_user.plan == 'free' else []
    return render_template('result.html', filename=filename, ads=ads)


@convert_bp.route('/download/<filename>')
def download(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
