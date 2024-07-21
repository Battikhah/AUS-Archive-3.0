import os
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, abort, session
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaIoBaseUpload
from io import BytesIO
from psycopg2 import pool
import pathlib
from google_auth_oauthlib.flow import Flow
from google.auth.transport import requests
from google.oauth2 import id_token
from pip._vendor import cachecontrol
import google.auth.transport.requests
import requests



app = Flask(__name__)

load_dotenv("lock.env")

app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = os.urandom(24)

# GOOGLE DRIVE API VARIABLES
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'AUS-ARCHIVER.json'
PARENT_FOLDER_ID = "1n_JeiBFdlxebfC6itq2VLe_dpGF272ya"

# GOOGLE LOG IN VARIABLES

######
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
######

GOOGLE_CLIENT_ID = "580529357076-s9n138qr90qbbjuuqso3d92o8vljedpm.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")
flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/callback"
)

def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return redirect(url_for("login"))
        else:
            return function()
    return wrapper

@app.route("/login")
def login():
    print("Login")
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/callback")
def callback():
    print("Callback")
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    session["email"] = id_info.get("email")
    return redirect(url_for("upload_file"))

# NEON (Postgres) SIDE VARIABLES
CONNECTION_STRING = os.getenv('DATABASE_URL')
CONNECTION_POOL = pool.SimpleConnectionPool(1, 250, CONNECTION_STRING)

if CONNECTION_POOL:
    print('Connection pool created successfully')

def init_db():
    with CONNECTION_POOL.getconn() as conn:
        cursor = conn.cursor()
        # File Metadata Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id SERIAL PRIMARY KEY,
                filename TEXT NOT NULL,
                course TEXT NOT NULL,
                profs TEXT NOT NULL,
                year INTEGER NOT NULL,
                semester TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_ID TEXT NOT NULL,
                file_link TEXT NOT NULL,
                uploaded_by TEXT NOT NULL
            )
        ''')
        # Course Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL
            )
        ''')
        # Professors Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS professors (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL
            )
        ''')
        # File Types Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_types (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL
            )
        ''')
        # Years Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS years (
                id SERIAL PRIMARY KEY,
                name INTEGER NOT NULL  -- Changed from TEXT to INTEGER
            )
        ''')
        # Semesters Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS semesters (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL
            )
        ''')
        # Suggestions Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suggestions (
                id SERIAL PRIMARY KEY,
                suggestion TEXT NOT NULL
            )
        ''')
        
        cursor.execute('SELECT COUNT(*) FROM professors')
        count = cursor.fetchone()[0]
        if count == 0:
            files = ['Names/names SBA.txt', 'Names/names CEN.txt', 'Names/names CAS.txt', 'Names/names CAAD.txt']
            done_name = []
            for i in files:
                with open(i, 'r') as file:
                    names = file.readlines()
                    for name in names:
                        name = name.strip()                    
                        if name:  
                            if name not in done_name: 
                                done_name.append(name)
                                cursor.execute('INSERT INTO professors (name) VALUES (%s)', (name,))

        cursor.execute('SELECT COUNT(*) FROM courses')
        count = cursor.fetchone()[0]
        if count == 0:
            files = ['Names/Courses.txt']
            done_name = []
            for i in files:
                with open(i, 'r') as file:
                    names = file.readlines()
                    for name in names:
                        name = name.strip()                    
                        if name:  
                            if name not in done_name: 
                                done_name.append(name)
                                cursor.execute('INSERT INTO courses (name) VALUES (%s)', (name,))
        
        cursor.execute('SELECT COUNT(*) FROM semesters') 
        count = cursor.fetchone()[0]
        if count == 0:
            files = ['Fall', 'Spring', 'Summer', 'Unkown']
            for name in files:
                cursor.execute('INSERT INTO semesters (name) VALUES (%s)', (name,))
        
        cursor.execute('SELECT COUNT(*) FROM file_types')
        count = cursor.fetchone()[0]
        if count == 0:
            files = ['Midterm 1', 'Midterm 2', 'Midterm 3', 'Final', 'Quiz', 'Assignment', 'Notes', 'Syllabus', 'Book', 'Book Answer Key','Others']
            for name in files:
                cursor.execute('INSERT INTO file_types (name) VALUES (%s)', (name,))

init_db()

# GOOGLE DRIVE API SIDE
def authenticate():
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return creds

def google_upload(file, file_name):
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': file_name,
        'parents': [PARENT_FOLDER_ID]
    }
    
    media = MediaIoBaseUpload(BytesIO(file.read()), mimetype='application/octet-stream', resumable=True)
    file.seek(0)
    
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print('File ID: %s' % file.get('id'))
    return file.get('id')

def google_retrieve_links(file_id):
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)

    file = service.files().get(fileId=file_id, fields='webViewLink').execute()
    link = file.get('webViewLink')
    return link

# ROUTES
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if not session.get('google_id'):
        return redirect(url_for('login_page'))
    else:
        if request.method == 'POST':
            course = request.form['course']
            profs = ', '.join(request.form.getlist('profs'))
            file_type = request.form['file_type']
            year = request.form['year']
            semester = request.form['semester']
            file = request.files['file']
            filename = f"{course[:7]}-{file_type}-{profs}-{semester}-{year}{os.path.splitext(file.filename)[1]}"
            user_email = session.get("email")
            
            file_ID = google_upload(file, filename)
            file_link = google_retrieve_links(file_ID)
            
            with CONNECTION_POOL.getconn() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO files (filename, course, profs, year, semester, file_type, file_ID, file_link, uploaded_by) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (filename, course, profs, year, semester, file_type, file_ID, file_link, user_email))
                conn.commit()
            
            return redirect(url_for('index'))
        
        courses = get_unique_values('courses')
        professors = get_unique_values('professors')
        semesters = get_unique_values('semesters')
        file_types = get_unique_values('file_types')
        return render_template('upload.html', courses=courses, professors=professors, semesters=semesters, file_types=file_types)


@app.route('/search', methods=['GET', 'POST'])
def search():
    files = []
    if request.method == 'POST':
        course = request.form.get('course', '')
        profs = request.form.getlist('prof')
        file_type = request.form.get('file_type', '')
        year = request.form.get('year', '')
        semester = request.form.get('semester', '')

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

        with CONNECTION_POOL.getconn() as conn:
            cursor = conn.cursor()
            cursor.execute(query, search_values)
            files = cursor.fetchall()
    
    courses = get_unique_values('courses')
    professors = get_unique_values('professors')
    semesters = get_unique_values('semesters')
    file_types = get_unique_values('file_types')
    return render_template('search.html', courses=courses, professors=professors, semesters=semesters, files=files, file_types=file_types)

@app.route('/view_by_course')
def view_by_course():
    files_by_course = {}
    with CONNECTION_POOL.getconn() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM files')
        files = cursor.fetchall()
        
        for file in files:
            course = file[2]
            if course not in files_by_course:
                files_by_course[course] = []
            files_by_course[course].append(file)

    return render_template('view_by_course.html', files_by_course=files_by_course)

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == os.getenv('ADMIN_PASSWORD'):
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            abort(401)
    else:
        return render_template('admin_login.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    course = request.form.get('course')
    prof = request.form.get('prof')
    semester = request.form.get('semester')
    suggestion = request.form.get('suggestion')
    
    with CONNECTION_POOL.getconn() as conn:
        cursor = conn.cursor()
        if course:
            cursor.execute('INSERT INTO courses (name) VALUES (%s)', (course,))
        if prof:
            cursor.execute('INSERT INTO professors (name) VALUES (%s)', (prof,))
        if semester:
            cursor.execute('INSERT INTO semesters (name) VALUES (%s)', (semester,))
        if suggestion:
            cursor.execute('INSERT INTO suggestions (suggestion) VALUES (%s)', (suggestion,))
        conn.commit()

    courses = get_unique_values('courses')
    professors = get_unique_values('professors')
    semesters = get_unique_values('semesters')
    suggestions = get_all_suggestions()
    return render_template('admin.html', courses=courses, professors=professors, semesters=semesters, suggestions=suggestions)


    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/submit_suggestion', methods=['POST'])
def submit_suggestion():
    suggestion = request.form.get('suggestion')
    if suggestion:
        with CONNECTION_POOL.getconn() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO suggestions (suggestion) VALUES (%s)', (suggestion,))
            conn.commit()
    return redirect(url_for('index'))

def get_unique_values(table):
    with CONNECTION_POOL.getconn() as conn:
        cursor = conn.cursor()
        query = f'SELECT name FROM {table}'
        cursor.execute(query)
        values = [row[0] for row in cursor.fetchall()]
    return values

def get_all_suggestions():
    with CONNECTION_POOL.getconn() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT suggestion FROM suggestions')
        suggestions = [row[0] for row in cursor.fetchall()]
    return suggestions

@app.route('/login_page', methods=['GET'])
def login_page():
    return render_template("login.html")

if __name__ == '__main__':
    app.run(debug=True)