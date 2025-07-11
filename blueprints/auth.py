from flask import Blueprint, render_template, redirect, url_for, session, request
import logging
import os
import pathlib
import urllib.request
import json
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
import cachecontrol
import requests as req
import google.auth.transport.requests

auth_bp = Blueprint('auth', __name__)

# Initialize OAuth client
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
client_secrets_file = os.path.join(pathlib.Path(__file__).parent.parent, "client_secret.json")

# Create OAuth flow
def get_oauth_flow():
    return Flow.from_client_secrets_file(
        client_secrets_file=client_secrets_file,
        scopes=["https://www.googleapis.com/auth/userinfo.profile", 
                "https://www.googleapis.com/auth/userinfo.email", 
                "openid"],
        redirect_uri="http://127.0.0.1:5000/auth/callback"
        # Use the following for production:
        # redirect_uri="https://ausarchive.vercel.app/auth/callback"
    )

def login_is_required(function):
    """Decorator to require login for routes"""
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return redirect(url_for("auth.login_page"))
        else:
            return function(*args, **kwargs)
    return wrapper

@auth_bp.route("/login")
def login():
    """Start OAuth login flow"""
    logging.debug("Login route accessed")
    flow = get_oauth_flow()
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@auth_bp.route("/callback")
def callback():
    """Handle OAuth callback"""
    logging.info("Callback route accessed with args: %s", request.args)
    try:
        flow = get_oauth_flow()
        
        # Ensure 'state' exists in the session and matches
        if "state" not in session:
            logging.error("'state' key not found in session")
            session['flash_message'] = "Authentication error: session state missing"
            session['flash_category'] = "danger"
            return redirect(url_for('main.index'))
            
        logging.info("Session state: %s, Request state: %s", session.get("state"), request.args.get("state"))
        if not session["state"] == request.args.get("state"):
            logging.error("State does not match!")
            session['flash_message'] = "Authentication error: state mismatch"
            session['flash_category'] = "danger"
            return redirect(url_for('main.index'))
        
        # Fetch token and validate
        logging.info("Fetching token...")
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials
        logging.info("Token fetched successfully")
        
        request_session = req.session()
        cached_session = cachecontrol.CacheControl(request_session)
        token_request = google.auth.transport.requests.Request(session=cached_session)

        logging.info("Getting user info from Google...")
        # Use the access token to get user info from Google's userinfo endpoint
        # This is more reliable than trying to verify the ID token
        userinfo_url = f"https://www.googleapis.com/oauth2/v1/userinfo?access_token={credentials.token}"
        try:
            with urllib.request.urlopen(userinfo_url) as response:
                id_info = json.loads(response.read().decode())
            logging.info("User info retrieved successfully from userinfo endpoint")
        except Exception as e:
            logging.error(f"Failed to get user info: {e}")
            raise
        
        # Log the user info received
        logging.info(f"Raw user info from Google: {id_info}")
        
        user_email = id_info.get("email")
        user_name = id_info.get("name")
        # The userinfo endpoint uses 'id' instead of 'sub' for the user ID
        user_id = id_info.get("id") or id_info.get("sub")
        
        logging.info(f"User info received - ID: {user_id}, Name: {user_name}, Email: {user_email}")
        
        # Check if email is from AUS domain
        if not user_email or not user_email.endswith("@aus.edu"):
            logging.warning(f"Non-AUS email attempted login: {user_email}")
            session['flash_message'] = "Please use your AUS email (@aus.edu) to log in"
            session['flash_category'] = "danger"
            return redirect(url_for('auth.login_page'))
        
        # Store user info in session
        session["google_id"] = user_id
        session["name"] = user_name
        session["email"] = user_email
        
        logging.info(f"Session updated with user info: {user_email}")
        
        # Add success message
        session['flash_message'] = f"Welcome, {session['name']}!"
        session['flash_category'] = "success"
        
        # Log login for analytics
        logging.info(f"User logged in successfully: {session['email']}")
        
        # Redirect to the saved URL if available
        next_url = session.pop('next_url', None)
        if next_url:
            logging.info(f"Redirecting to requested URL: {next_url}")
            return redirect(next_url)
        else:
            logging.info("No next URL found, redirecting to upload page")
            return redirect(url_for("files.upload_file"))
        
    except Exception as e:
        logging.error(f"Error during OAuth callback: {str(e)}")
        session['flash_message'] = "Authentication error occurred"
        session['flash_category'] = "danger"
        return redirect(url_for('main.index'))

@auth_bp.route('/login_page', methods=['GET'])
def login_page():
    """Show login page"""
    return render_template("login.html", current_year=2025)

@auth_bp.route('/logout')
def logout():
    """Log user out by clearing session"""
    if session.get('google_id'):
        email = session.get('email', 'Unknown')
        logging.info(f"User logged out: {email}")
        
    # Clear session data
    session.clear()
    
    # Add logout message
    session['flash_message'] = "You have been logged out successfully"
    session['flash_category'] = "info"
    
    return redirect(url_for('main.index'))
