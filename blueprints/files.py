from flask import Blueprint, render_template, request, redirect, url_for, session, abort, current_app
import logging
from io import BytesIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import os
from functools import wraps

files_bp = Blueprint('files', __name__)

# Decorator to check if user is logged in
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('google_id') or not session.get('email'):
            logging.warning("Authentication required but user not logged in")
            session['flash_message'] = "Please log in to access this page"
            session['flash_category'] = "warning"
            # Save the requested URL for redirecting after authentication
            session['next_url'] = request.url
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated_function

def authenticate():
    """Authenticate with Google Drive API"""
    try:
        # Try to use helper function first (supports both local and Vercel)
        from app import get_service_account_credentials
        credentials_data = get_service_account_credentials()
        if credentials_data:
            SCOPES = os.getenv("DRIVE_SCOPES", "").split(",")
            return service_account.Credentials.from_service_account_info(credentials_data, scopes=SCOPES)
    except Exception as e:
        logging.error(f"Failed to get credentials from helper function: {e}")
    
    # Fallback to local file approach
    SCOPES = os.getenv("DRIVE_SCOPES", "").split(",")
    SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
    
    if SERVICE_ACCOUNT_FILE and os.path.exists(SERVICE_ACCOUNT_FILE):
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        return creds
    
    raise Exception("No service account credentials found")

def google_upload(file, file_name):
    """Upload file to Google Drive"""
    PARENT_FOLDER_ID = os.getenv("PARENT_FOLDER_ID")
    
    logging.debug("Authenticating for Google Drive API")
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': file_name,
        'parents': [PARENT_FOLDER_ID]
    }
    
    media = MediaIoBaseUpload(BytesIO(file.read()), mimetype='application/octet-stream', resumable=True)
    file.seek(0)
    
    try:
        logging.debug("Uploading file to Google Drive")
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        logging.debug('File ID: %s', file.get('id'))
        return file.get('id')
    except Exception as e:
        logging.error("An error occurred during file upload: %s", e)
        raise

def google_retrieve_links(file_ID):
    """Retrieve shareable link for uploaded file"""
    logging.debug("Retrieving links for uploaded file")
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)
    
    # Make the file publicly accessible
    permission = {
        'type': 'anyone',
        'role': 'reader',
    }
    service.permissions().create(fileId=file_ID, body=permission).execute()
    
    # Get the shareable link
    file = service.files().get(fileId=file_ID, fields='webViewLink').execute()
    return file['webViewLink']

def process_drive_link(drive_url, course, file_type, profs, semester, year):
    """Process Google Drive link and extract file information"""
    import re
    
    try:
        # Extract file ID from various Google Drive URL formats
        file_id = extract_drive_file_id(drive_url)
        if not file_id:
            return None, None, None
        
        # Try to get file information from Google Drive API
        try:
            from app import get_service_account_credentials
            credentials_data = get_service_account_credentials()
            if credentials_data:
                creds = service_account.Credentials.from_service_account_info(
                    credentials_data, 
                    scopes=os.getenv("DRIVE_SCOPES", "").split(",")
                )
                service = build('drive', 'v3', credentials=creds)
                
                # Get file information
                file_info = service.files().get(fileId=file_id, fields='name,mimeType,webViewLink').execute()
                
                # Create a descriptive filename
                original_name = file_info.get('name', 'Unknown')
                file_extension = os.path.splitext(original_name)[1] or get_extension_from_mimetype(file_info.get('mimeType', ''))
                filename = f"{course[:7]}-{file_type}-{profs}-{semester}-{year}-{original_name}"
                
                return file_id, filename, file_info['webViewLink']
        except Exception as e:
            logging.warning(f"Could not access file info via API: {e}")
        
        # Fallback: create filename without API access
        filename = f"{course[:7]}-{file_type}-{profs}-{semester}-{year}-SharedLink"
        
        # Return the provided URL as the link (user must ensure it's shareable)
        return file_id, filename, drive_url
        
    except Exception as e:
        logging.error(f"Error processing drive link: {e}")
        return None, None, None

def extract_drive_file_id(url):
    """Extract file ID from Google Drive URL"""
    import re
    
    # Common Google Drive URL patterns
    patterns = [
        r'/file/d/([a-zA-Z0-9-_]+)',  # https://drive.google.com/file/d/FILE_ID/view
        r'/document/d/([a-zA-Z0-9-_]+)',  # Google Docs
        r'/spreadsheets/d/([a-zA-Z0-9-_]+)',  # Google Sheets
        r'/presentation/d/([a-zA-Z0-9-_]+)',  # Google Slides
        r'id=([a-zA-Z0-9-_]+)',  # Query parameter format
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def get_extension_from_mimetype(mimetype):
    """Get file extension from MIME type"""
    mime_to_ext = {
        'application/pdf': '.pdf',
        'application/msword': '.doc',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        'application/vnd.ms-powerpoint': '.ppt',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
        'application/vnd.ms-excel': '.xls',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
        'application/vnd.google-apps.document': '.gdoc',
        'application/vnd.google-apps.spreadsheet': '.gsheet',
        'application/vnd.google-apps.presentation': '.gslides',
    }
    return mime_to_ext.get(mimetype, '')

def get_unique_values(table):
    """Get unique values from a database table"""
    from app import CONNECTION_POOL
    
    with CONNECTION_POOL.getconn() as conn:
        cursor = conn.cursor()
        query = f'SELECT name FROM {table}'
        cursor.execute(query)
        values = [row[0] for row in cursor.fetchall()]
    return values

def validate_file(file):
    """Validate file type and size"""
    # Check if file is provided
    if not file or file.filename == '':
        return False, "No file selected"
        
    # Check allowed extensions
    allowed_extensions = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'zip'}
    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    
    if file_ext not in allowed_extensions:
        return False, f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
    
    # Check file size (limit to 10MB)
    if len(file.read()) > 10 * 1024 * 1024:  # 10MB in bytes
        file.seek(0)
        return False, "File size exceeds 10MB limit"
    
    file.seek(0)
    return True, "File is valid"

@files_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    """Upload file page and handler"""
    from app import CONNECTION_POOL
        
    if request.method == 'POST':
        logging.debug("Processing file upload")
        # Get form data
        course = request.form['course']
        profs = ', '.join(request.form.getlist('profs'))
        file_type = request.form['file_type']
        year = request.form['year']
        semester = request.form['semester']
        upload_method = request.form.get('upload_method', 'file')
        
        user_email = session.get("email")
        
        if upload_method == 'drive_link':
            # Handle Google Drive link
            drive_url = request.form['drive_url']
            
            # Validate and process Drive URL
            file_ID, filename, file_link = process_drive_link(drive_url, course, file_type, profs, semester, year)
            if not file_ID:
                session['flash_message'] = "Invalid Google Drive link. Please check the URL and sharing permissions."
                session['flash_category'] = "danger"
                return redirect(url_for('files.upload_file'))
        else:
            # Handle file upload
            file = request.files['file']
            
            # Validate file
            is_valid, message = validate_file(file)
            if not is_valid:
                session['flash_message'] = message
                session['flash_category'] = "danger"
                return redirect(url_for('files.upload_file'))
                
            # Create filename
            file_extension = os.path.splitext(file.filename or '')[1]
            filename = f"{course[:7]}-{file_type}-{profs}-{semester}-{year}{file_extension}"
            
            try:
                # Upload to Google Drive
                file_ID = google_upload(file, filename)
                file_link = google_retrieve_links(file_ID)
            except Exception as e:
                logging.error(f"Google Drive upload failed: {str(e)}")
                session['flash_message'] = "Upload failed. Please try again."
                session['flash_category'] = "danger"
                return redirect(url_for('files.upload_file'))
        
        try:
            # Save to database
            with CONNECTION_POOL.getconn() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO files (filename, course, profs, year, semester, file_type, file_ID, file_link, uploaded_by) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (filename, course, profs, year, semester, file_type, file_ID, file_link, user_email))
                conn.commit()
            
            # Add success message
            session['flash_message'] = "Resource shared successfully!" if upload_method == 'drive_link' else "File uploaded successfully!"
            session['flash_category'] = "success"
            
            # Log upload for analytics
            logging.info(f"{'Drive link' if upload_method == 'drive_link' else 'File'} uploaded: {course}, {file_type}, by: {user_email}")
            
            # Record upload in analytics
            import requests
            try:
                file_info = {
                    'course': course,
                    'file_type': file_type,
                    'professor': profs,
                    'year': year,
                    'semester': semester
                }
                requests.post(
                    request.url_root.rstrip('/') + '/analytics/api/analytics/record-upload',
                    json={'file_info': file_info},
                    timeout=1  # Non-blocking
                )
            except Exception as e:
                logging.error(f"Failed to record upload analytics: {str(e)}")
            
            return redirect(url_for('main.index'))
        except Exception as e:
            logging.error(f"Error uploading file: {str(e)}")
            session['flash_message'] = f"Error uploading file: {str(e)}"
            session['flash_category'] = "danger"
            return redirect(url_for('files.upload_file'))
    
    # GET request - show upload form
    courses = get_unique_values('courses')
    professors = get_unique_values('professors')
    semesters = get_unique_values('semesters')
    file_types = get_unique_values('file_types')
    return render_template('upload.html', 
                          courses=courses, 
                          professors=professors, 
                          semesters=semesters, 
                          file_types=file_types,
                          current_year=2025)

@files_bp.route('/search', methods=['GET', 'POST'])
def search():
    """Search files page and handler"""
    from app import CONNECTION_POOL
    
    files = []
    if request.method == 'POST':
        # Get search parameters
        course = request.form.get('course', '')
        profs = request.form.getlist('prof')
        file_type = request.form.get('file_type', '')
        year = request.form.get('year', '')
        semester = request.form.get('semester', '')

        # Build query with parameters
        query = "SELECT *, file_link FROM files WHERE 1=1"
        search_values = []
        
        if course:
            query += ' AND course=%s'
            search_values.append(course)
            
        if profs:
            query += ' AND (' + ' OR '.join(['profs LIKE %s'] * len(profs)) + ')'
            search_values.extend([f"%{prof}%" for prof in profs])
            
        if year:
            query += ' AND year=%s'
            search_values.append(year)
            
        if semester:
            query += ' AND semester=%s'
            search_values.append(semester)
            
        if file_type:
            query += ' AND file_type=%s'
            search_values.append(file_type)
            
        # Add ordering
        query += ' ORDER BY id DESC'

        # Execute search
        try:
            with CONNECTION_POOL.getconn() as conn:
                cursor = conn.cursor()
                cursor.execute(query, search_values)
                files = cursor.fetchall()
                
                # Log search for analytics
                search_params = {
                    'course': course,
                    'profs': profs,
                    'file_type': file_type, 
                    'year': year,
                    'semester': semester,
                    'results_count': len(files)
                }
                logging.info(f"Search performed: {search_params}")
                
                # Record search in analytics
                import requests
                try:
                    requests.post(
                        request.url_root.rstrip('/') + '/analytics/api/analytics/record-search',
                        json={'params': search_params, 'results_count': len(files)},
                        timeout=1  # Non-blocking
                    )
                except Exception as e:
                    logging.error(f"Failed to record search analytics: {str(e)}")
        except Exception as e:
            logging.error(f"Error during search: {str(e)}")
            session['flash_message'] = f"Error during search: {str(e)}"
            session['flash_category'] = "danger"
    
    # Get data for search form
    courses = get_unique_values('courses')
    professors = get_unique_values('professors')
    semesters = get_unique_values('semesters')
    file_types = get_unique_values('file_types')
    
    return render_template('search.html', 
                          courses=courses, 
                          professors=professors, 
                          semesters=semesters, 
                          files=files, 
                          file_types=file_types,
                          current_year=2025)
