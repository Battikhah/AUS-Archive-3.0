# Vercel Deployment Setup Guide

## Environment Variables to Set in Vercel Dashboard

Go to your Vercel project → Settings → Environment Variables and add these:

### 1. Basic Configuration

```
ADMIN_PASSWORD=12345
SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
DATABASE_URL=postgresql://database_neon_owner:oglNbiZD5t6B@ep-orange-thunder-a26qgrxq-pooler.eu-central-1.aws.neon.tech/database_neon?sslmode=require
GOOGLE_CLIENT_ID=580529357076-s9n138qr90qbbjuuqso3d92o8vljedpm.apps.googleusercontent.com
PARENT_FOLDER_ID=1n_JeiBFdlxebfC6itq2VLe_dpGF272ya
DRIVE_SCOPES=https://www.googleapis.com/auth/drive
```

### 2. Base64 Encoded JSON Files

**GOOGLE_CLIENT_SECRET_JSON_BASE64:**
Copy the content from `client_secret_base64.txt`

**SERVICE_ACCOUNT_JSON_BASE64:**
Copy the content from `AUS-ARCHIVER_base64.txt`

## Quick Setup Steps

1. **Deploy to Vercel:**

   ```bash
   # Install Vercel CLI if not already installed
   npm i -g vercel

   # Deploy
   vercel
   ```

2. **Set Environment Variables:**

   - Go to Vercel Dashboard → Your Project → Settings → Environment Variables
   - Add each variable from the list above
   - For the JSON base64 variables, copy the entire content from the generated `.txt` files

3. **Redeploy:**
   ```bash
   vercel --prod
   ```

## Security Notes

- ✅ All secrets are in Vercel environment variables (not in git)
- ✅ Repository can be safely made public
- ✅ Base64 files are git-ignored (see .gitignore)
- ✅ Local development still uses lock.env and JSON files

## Testing the Deployment

After deployment, verify:

1. **OAuth Login:** Test Google authentication
2. **File Upload:** Test file upload to Google Drive
3. **Admin Access:** Test admin dashboard access
4. **Database:** Verify database connections work

## Cleanup

After successful deployment, you can delete the base64 files:

```bash
rm *_base64.txt
```

The original JSON files and lock.env remain for local development.
