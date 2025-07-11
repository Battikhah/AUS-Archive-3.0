# Deployment Guide: Managing Private Keys and Public Repository

This guide explains how to handle deployment with private keys while maintaining a public repository.

## Option 1: Environment Variables (Recommended)

Keep secrets out of git entirely and use environment variables for deployment.

### For Vercel Deployment:

1. **Set up environment variables in Vercel dashboard:**

   ```
   ADMIN_PASSWORD=your_admin_password
   SECRET_KEY=your_secret_key
   DATABASE_URL=postgresql://username:password@host:port/database?sslmode=require
   GOOGLE_CLIENT_ID=your_google_client_id.apps.googleusercontent.com
   PARENT_FOLDER_ID=your_google_drive_folder_id
   DRIVE_SCOPES=https://www.googleapis.com/auth/drive
   ```

2. **For JSON credential files, encode them as base64:**

   ```bash
   # Encode client_secret.json
   base64 -i client_secret.json | tr -d '\n'
   # Copy the output and add as: GOOGLE_CLIENT_SECRET_JSON_BASE64

   # Encode AUS-ARCHIVER.json
   base64 -i AUS-ARCHIVER.json | tr -d '\n'
   # Copy the output and add as: SERVICE_ACCOUNT_JSON_BASE64
   ```

3. **The app automatically detects the environment:**
   - Local development: Uses `lock.env` and JSON files
   - Vercel deployment: Uses environment variables

### Benefits:

- ✅ No secrets in git repository
- ✅ Repository can be public
- ✅ Secure deployment
- ✅ Easy to manage different environments

## Option 2: Separate Branches

Maintain two branches with different purposes:

### Setup:

```bash
# 1. Current main branch (public-safe)
git checkout main
# Keep comprehensive .gitignore excluding all secrets

# 2. Create deployment branch (with secrets)
git checkout -b deployment

# 3. Modify .gitignore for deployment
cat > .gitignore << 'EOF'
# Deployment branch - minimal exclusions
.venv/
__pycache__/
*.pyc
.DS_Store
demos/
# Allow secrets for deployment
EOF

# 4. Add secrets to deployment branch
git add lock.env client_secret.json AUS-ARCHIVER.json .gitignore
git commit -m "deployment: Add secrets for deployment"

# 5. Push both branches
git push origin main        # Public-safe branch
git push origin deployment  # Private branch with secrets
```

### Usage:

- **Public repository:** Point to `main` branch
- **Vercel deployment:** Deploy from `deployment` branch
- **Development:** Work on `main` branch, merge changes to `deployment`

### Workflow:

```bash
# Make changes on main
git checkout main
# ... make changes ...
git commit -m "feature: Add new functionality"
git push origin main

# Merge to deployment
git checkout deployment
git merge main
git push origin deployment  # Triggers Vercel deployment
```

## Option 3: Separate Repositories

### Setup:

1. **Private Repository** (`AUS-Archive-3.0-private`)

   - Contains all files including secrets
   - Used for deployment
   - Private GitHub repository

2. **Public Repository** (`AUS-Archive-3.0`)
   - Clean version without secrets
   - Public GitHub repository
   - Points people to setup instructions

### Workflow:

```bash
# Push to private repo (with secrets)
git remote add private git@github.com:yourusername/AUS-Archive-3.0-private.git
git push private main

# Clean and push to public repo
git rm --cached lock.env client_secret.json AUS-ARCHIVER.json
git commit -m "Remove secrets for public release"
git remote add public git@github.com:yourusername/AUS-Archive-3.0.git
git push public main
```

## Recommended Approach

**Use Option 1 (Environment Variables)** because:

- Most secure (no secrets in git)
- Single repository to maintain
- Works with any deployment platform
- Industry best practice
- Repository can be safely public

## Security Checklist

- [ ] All secrets are in environment variables or ignored by git
- [ ] `.env.example` shows required configuration without actual values
- [ ] `README.md` has clear setup instructions
- [ ] No API keys, passwords, or tokens in git history
- [ ] Production and development use different databases
- [ ] Regular rotation of API keys and secrets
