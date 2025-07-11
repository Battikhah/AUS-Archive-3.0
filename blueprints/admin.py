from flask import Blueprint, render_template, request, redirect, url_for, session, abort
import logging
import os

admin_bp = Blueprint('admin', __name__)

# Admin authentication decorator
def admin_required(f):
    """Decorator to require admin authentication"""
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            session['flash_message'] = "Administrator login required"
            session['flash_category'] = "warning"
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == os.getenv('ADMIN_PASSWORD'):
            session['admin_logged_in'] = True
            session['flash_message'] = "Welcome, Administrator!"
            session['flash_category'] = "success"
            return redirect(url_for('admin.admin_panel'))
        else:
            session['flash_message'] = "Invalid password"
            session['flash_category'] = "danger"
            return render_template('admin_login.html')
    else:
        return render_template('admin_login.html')

@admin_bp.route('/admin', methods=['GET', 'POST'])
@admin_required
def admin_panel():
    """Admin panel for managing courses, professors, semesters, and suggestions"""
    from app import CONNECTION_POOL

    # Handle form submissions
    course = request.form.get('course')
    prof = request.form.get('prof')
    semester = request.form.get('semester')
    suggestion = request.form.get('suggestion')
    
    try:
        with CONNECTION_POOL.getconn() as conn:
            cursor = conn.cursor()
            
            # Add new course
            if course:
                cursor.execute('INSERT INTO courses (name) VALUES (%s)', (course,))
                session['flash_message'] = f"Course '{course}' added successfully"
                session['flash_category'] = "success"
                
            # Add new professor
            if prof:
                cursor.execute('INSERT INTO professors (name) VALUES (%s)', (prof,))
                session['flash_message'] = f"Professor '{prof}' added successfully"
                session['flash_category'] = "success"
                
            # Add new semester
            if semester:
                cursor.execute('INSERT INTO semesters (name) VALUES (%s)', (semester,))
                session['flash_message'] = f"Semester '{semester}' added successfully"
                session['flash_category'] = "success"
                
            # Add new suggestion
            if suggestion:
                cursor.execute('INSERT INTO suggestions (suggestion) VALUES (%s)', (suggestion,))
                session['flash_message'] = f"Suggestion added successfully"
                session['flash_category'] = "success"
                
            conn.commit()
    except Exception as e:
        logging.error(f"Admin panel error: {str(e)}")
        session['flash_message'] = f"An error occurred: {str(e)}"
        session['flash_category'] = "danger"
    
    # Get data for admin panel
    with CONNECTION_POOL.getconn() as conn:
        cursor = conn.cursor()
        
        # Get all reported files
        cursor.execute('SELECT * FROM files WHERE reported=TRUE')
        reported_files = cursor.fetchall()
        
        # Get unique values for dropdowns
        def get_unique_values(table):
            cursor.execute(f'SELECT name FROM {table}')
            return [row[0] for row in cursor.fetchall()]
        
        courses = get_unique_values('courses')
        professors = get_unique_values('professors')
        semesters = get_unique_values('semesters')
        
        # Get all suggestions
        cursor.execute('SELECT suggestion, id FROM suggestions ORDER BY id DESC')
        suggestions = cursor.fetchall()

    return render_template('admin.html', 
                          courses=courses, 
                          professors=professors, 
                          semesters=semesters, 
                          suggestions=suggestions,
                          reported_files=reported_files)

@admin_bp.route('/admin/delete_suggestion/<int:suggestion_id>', methods=['POST'])
def delete_suggestion(suggestion_id):
    """Delete a suggestion"""
    from app import CONNECTION_POOL
    
    if not session.get('admin_logged_in'):
        abort(403)
        
    try:
        with CONNECTION_POOL.getconn() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM suggestions WHERE id = %s', (suggestion_id,))
            conn.commit()
            session['flash_message'] = "Suggestion deleted successfully"
            session['flash_category'] = "success"
    except Exception as e:
        logging.error(f"Error deleting suggestion: {str(e)}")
        session['flash_message'] = f"Error deleting suggestion: {str(e)}"
        session['flash_category'] = "danger"
        
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/admin/resolve_report/<int:file_id>', methods=['POST'])
def resolve_report(file_id):
    """Mark a reported file as resolved"""
    from app import CONNECTION_POOL
    
    if not session.get('admin_logged_in'):
        abort(403)
        
    try:
        with CONNECTION_POOL.getconn() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE files SET reported = FALSE WHERE id = %s', (file_id,))
            conn.commit()
            session['flash_message'] = "Report marked as resolved"
            session['flash_category'] = "success"
    except Exception as e:
        logging.error(f"Error resolving report: {str(e)}")
        session['flash_message'] = f"Error resolving report: {str(e)}"
        session['flash_category'] = "danger"
        
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/admin/delete_file/<int:file_id>', methods=['POST'])
def delete_file(file_id):
    """Delete a file from the database"""
    from app import CONNECTION_POOL
    
    if not session.get('admin_logged_in'):
        abort(403)
        
    try:
        with CONNECTION_POOL.getconn() as conn:
            cursor = conn.cursor()
            # Get file ID from Google Drive before deleting
            cursor.execute('SELECT file_ID FROM files WHERE id = %s', (file_id,))
            result = cursor.fetchone()
            
            if result:
                drive_file_id = result[0]
                
                # Delete from database
                cursor.execute('DELETE FROM files WHERE id = %s', (file_id,))
                conn.commit()
                
                # TODO: Also delete from Google Drive in a future enhancement
                session['flash_message'] = f"File deleted from database. Google Drive file ID: {drive_file_id}"
                session['flash_category'] = "success"
            else:
                session['flash_message'] = "File not found"
                session['flash_category'] = "warning"
    except Exception as e:
        logging.error(f"Error deleting file: {str(e)}")
        session['flash_message'] = f"Error deleting file: {str(e)}"
        session['flash_category'] = "danger"
        
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/admin/analytics')
@admin_required
def analytics_dashboard():
    """Admin analytics dashboard"""
    return render_template('analytics_dashboard.html')
