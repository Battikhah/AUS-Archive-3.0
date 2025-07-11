import os
import logging
import datetime
import warnings
import json
import base64
from pathlib import Path
# Suppress the LibreSSL warning that appears on macOS
warnings.filterwarnings('ignore', message='.*OpenSSL.*LibreSSL.*')
from flask import Flask, render_template, session, flash, redirect, request
from flask_session import Session
from dotenv import load_dotenv
from psycopg2 import pool
from db import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
# Try to load from lock.env (local development), fall back to system env (production/Vercel)
load_dotenv("lock.env")

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configure app
    app.config['UPLOAD_FOLDER'] = 'uploads'
    
    # Static file configuration for production
    if os.getenv('VERCEL_URL') or os.getenv('VERCEL_ENV'):
        # In production, ensure static files are served properly
        app.static_url_path = '/static'
        app.static_folder = 'static'
    
    # Always use string secret key for Flask-Session
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        # Use a simple string secret key for development
        secret_key = 'development-secret-key-for-aus-archive'
    
    # Ensure secret key is a string and not bytes
    if isinstance(secret_key, bytes):
        secret_key = secret_key.decode('utf-8')
    
    app.secret_key = secret_key
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit uploads to 16MB

    # Create session directory if it doesn't exist (for potential future use)
    session_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_session')
    os.makedirs(session_dir, exist_ok=True)
    
    # Try minimal Flask-Session configuration to fix OAuth session issues
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = session_dir
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = False
    app.config['SESSION_KEY_PREFIX'] = ''
    
    # Initialize Flask-Session
    Session(app)
    
    # For Google authentication
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    
    # Register app context data
    @app.context_processor
    def inject_context():
        """Inject common variables into template context"""
        return {
            'current_year': datetime.datetime.now().year
        }
    
    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        """Handle 404 errors"""
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        """Handle 500 errors"""
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden(e):
        """Handle 403 errors"""
        # Log more details about what caused the 403
        logger.error(f"403 Forbidden error: {e}")
        logger.error(f"Request URL: {request.url}")
        logger.error(f"Request method: {request.method}")
        logger.error(f"Request headers: {dict(request.headers)}")
        logger.error(f"Session data: {dict(session)}")
        return render_template('errors/403.html'), 403
    
    # Process flash messages and log session info
    @app.before_request
    def process_flash_messages():
        """Process flash messages stored in session and log session info for debugging"""
        try:
            # Fix any localhost URLs in session when in production
            if (os.getenv('VERCEL_URL') or os.getenv('VERCEL_ENV')):
                if 'next_url' in session and session['next_url']:
                    if '127.0.0.1' in session['next_url'] or 'localhost' in session['next_url']:
                        logger.warning(f"Removing localhost next_url in production: {session['next_url']}")
                        session.pop('next_url', None)
            
            # Log session info for debugging (only for specific routes)
            debug_routes = ['/upload', '/auth/login', '/auth/callback']
            if any(route in request.path for route in debug_routes):
                google_id = session.get('google_id', 'None')
                if google_id and not isinstance(google_id, str):
                    google_id = str(google_id)
                logger.info(f"Session for {request.path}: google_id={google_id[:5] if google_id and google_id != 'None' else 'None'}..., "
                           f"name={session.get('name', 'None')}, "
                           f"email={session.get('email', 'None')}")
            
            if session and 'flash_message' in session and 'flash_category' in session:
                flash(session.pop('flash_message'), session.pop('flash_category'))
        except Exception as e:
            # Log the error but don't fail the request
            logger.error(f"Error processing flash messages: {e}")
    
    # Register blueprints
    from blueprints.main import main_bp
    from blueprints.auth import auth_bp
    from blueprints.files import files_bp
    from blueprints.admin import admin_bp
    from blueprints.analytics import analytics_bp
    from blueprints.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(files_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Handle legacy callback URL for backward compatibility
    @app.route("/callback")
    def legacy_callback():
        """Redirect legacy callback URL to the new blueprint path"""
        return redirect('/auth/callback' + ('?' + request.query_string.decode() if request.query_string else ''))
    
    return app
# Create database connection pool
CONNECTION_STRING = os.getenv('DATABASE_URL')
try:
    CONNECTION_POOL = pool.SimpleConnectionPool(1, 250, CONNECTION_STRING)
    logger.info('Connection pool created successfully')
except Exception as e:
    logger.error(f"Error creating connection pool: {e}")
    CONNECTION_POOL = None

# Application factory pattern
app = create_app()

# Make connection pool available to application context
app.config['CONNECTION_POOL'] = CONNECTION_POOL

# Helper functions for handling credentials in both local and production environments
def get_google_credentials():
    """Get Google credentials for both local development and Vercel deployment"""
    # Try to get from environment variable first (Vercel deployment)
    client_secret_base64 = os.getenv('GOOGLE_CLIENT_SECRET_JSON_BASE64')
    if client_secret_base64:
        try:
            # Decode base64 and parse JSON
            client_secret_json = base64.b64decode(client_secret_base64).decode('utf-8')
            return json.loads(client_secret_json)
        except Exception as e:
            logger.error(f"Failed to decode Google credentials from environment: {e}")
    
    # Fall back to local file (development)
    client_secrets_file = Path(__file__).parent / "client_secret.json"
    if client_secrets_file.exists():
        with open(client_secrets_file, 'r') as f:
            return json.load(f)
    
    logger.error("No Google credentials found in environment or local file")
    return None

def get_service_account_credentials():
    """Get service account credentials for both local development and Vercel deployment"""
    # Try to get from environment variable first (Vercel deployment)
    service_account_base64 = os.getenv('SERVICE_ACCOUNT_JSON_BASE64')
    if service_account_base64:
        try:
            # Decode base64 and parse JSON
            service_account_json = base64.b64decode(service_account_base64).decode('utf-8')
            return json.loads(service_account_json)
        except Exception as e:
            logger.error(f"Failed to decode service account credentials from environment: {e}")
    
    # Fall back to local file (development)
    service_account_file = os.getenv("SERVICE_ACCOUNT_FILE", "AUS-ARCHIVER.json")
    service_account_path = Path(__file__).parent / service_account_file
    if service_account_path.exists():
        with open(service_account_path, 'r') as f:
            return json.load(f)
    
    logger.error("No service account credentials found in environment or local file")
    return None

if __name__ == '__main__':
    logger.info("Starting Flask app")
    if CONNECTION_POOL:
        init_db(CONNECTION_POOL=CONNECTION_POOL)
    else:
        logger.error("Cannot initialize database: connection pool not available")
    
    app.run(debug=True)