from flask import Blueprint, render_template, request, redirect, url_for, session
import logging

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page route"""
    return render_template('index.html', current_year=2025)

@main_bp.route('/submit_suggestion', methods=['POST'])
def submit_suggestion():
    """Handle suggestion submissions from users"""
    from app import CONNECTION_POOL
    
    suggestion = request.form.get('suggestion')
    if suggestion:
        try:
            with CONNECTION_POOL.getconn() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO suggestions (suggestion) VALUES (%s)', (suggestion,))
                conn.commit()
            
            # Set flash message for success
            session['flash_message'] = "Thank you for your suggestion!"
            session['flash_category'] = "success"
        except Exception as e:
            logging.error(f"Error submitting suggestion: {str(e)}")
            session['flash_message'] = "Sorry, there was an issue submitting your suggestion."
            session['flash_category'] = "danger"
    
    return redirect(url_for('main.index'))

@main_bp.route('/about')
def about():
    """About page route"""
    return render_template('about.html', current_year=2025)

@main_bp.route('/contact')
def contact():
    """Contact page route"""
    return render_template('contact.html', current_year=2025)

@main_bp.route('/ads.txt')
def ads():
    """Serve ads.txt file for Google AdSense"""
    return render_template('ads.txt')

@main_bp.route('/report_file', methods=['POST'])
def report_file():
    """Handle file reporting by users"""
    from app import CONNECTION_POOL
    
    file_id = request.form.get('file_id')
    if file_id:
        try:
            with CONNECTION_POOL.getconn() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE files SET reported=TRUE WHERE id=%s', (file_id,))
                conn.commit()
                
            session['flash_message'] = "Thank you for reporting this file. Our team will review it."
            session['flash_category'] = "info"
        except Exception as e:
            logging.error(f"Error reporting file: {str(e)}")
            session['flash_message'] = "Sorry, there was an issue reporting this file."
            session['flash_category'] = "danger"
    
    return redirect(url_for('files.search'))
