# AUS Archive 3.0

A web application for AUS (American University of Sharjah) students to share and access academic resources.

## Features

- **Google OAuth Authentication** - Secure login with @aus.edu accounts only
- **File Upload & Management** - Upload and organize academic resources
- **Search Functionality** - Find files by course, professor, type, etc.
- **Admin Dashboard** - Administrative controls and analytics
- **Mobile Responsive** - Works on all devices

## Setup Instructions

### Prerequisites

- Python 3.9+
- PostgreSQL database
- Google Cloud Project with OAuth 2.0 and Drive API enabled

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd AUS-Archive-3.0
   ```

2. **Create virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**

   ```bash
   cp .env.example lock.env
   # Edit lock.env with your actual configuration values
   ```

5. **Google OAuth Setup**

   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Google Drive API and Google+ API
   - Create OAuth 2.0 credentials
   - Download the credentials as `client_secret.json`
   - Add authorized redirect URIs:
     - `http://127.0.0.1:5000/auth/callback` (development)
     - `https://yourdomain.com/auth/callback` (production)

6. **Google Service Account Setup**

   - Create a service account in Google Cloud Console
   - Download the service account key as `AUS-ARCHIVER.json`
   - Create a Google Drive folder and get its ID
   - Share the folder with the service account email

7. **Database Setup**

   - Set up a PostgreSQL database
   - Update the `DATABASE_URL` in `lock.env`

8. **Run the application**
   ```bash
   python app.py
   ```

The application will be available at `http://127.0.0.1:5000`

## Configuration Files

- `lock.env` - Environment variables and secrets
- `client_secret.json` - Google OAuth credentials
- `AUS-ARCHIVER.json` - Google service account key

**⚠️ Never commit these files to git!**

## Development

### Project Structure

```
AUS-Archive-3.0/
├── app.py                 # Main Flask application
├── db.py                  # Database initialization
├── blueprints/            # Flask blueprints
│   ├── auth.py           # Authentication routes
│   ├── files.py          # File upload/download routes
│   ├── main.py           # Main pages routes
│   ├── admin.py          # Admin dashboard routes
│   └── analytics.py      # Analytics routes
├── templates/             # HTML templates
├── static/                # CSS, JS, images
├── requirements.txt       # Python dependencies
└── .env.example          # Environment configuration example
```

### Running in Development

```bash
python app.py
```

The application runs in debug mode by default when executed directly.

## Security Notes

- Only @aus.edu email addresses can authenticate
- All sensitive files are in `.gitignore`
- Sessions are handled securely with Flask-Session
- File uploads are validated and size-limited

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational use at American University of Sharjah.
