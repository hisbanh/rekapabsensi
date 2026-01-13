# PythonAnywhere Deployment Guide

This guide provides step-by-step instructions for deploying the SIPA Yaumi application on PythonAnywhere.

## Prerequisites

- PythonAnywhere account (free or paid)
- Git repository with your code
- Basic knowledge of Django and command line

## Step 1: Clone Repository

1. Open a Bash console in PythonAnywhere
2. Clone your repository:
```bash
git clone https://github.com/hisbanh/rekapabsensi.git
cd rekapabsensi
```

## Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 4: Configure Environment Variables

Create a `.env` file in your project root:

```bash
nano .env
```

Add the following content:
```
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourusername.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://yourusername.pythonanywhere.com
```

Replace `yourusername` with your actual PythonAnywhere username.

## Step 5: Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Populate initial data (if needed)
python manage.py populate_students
```

## Step 6: Collect Static Files

```bash
python manage.py collectstatic --noinput
```

## Step 7: Configure Web App

1. Go to PythonAnywhere Dashboard → Web
2. Click "Add a new web app"
3. Choose "Manual configuration" → Python 3.11
4. Set the following configurations:

### Source code:
```
/home/yourusername/rekapabsensi
```

### Working directory:
```
/home/yourusername/rekapabsensi
```

### Virtualenv:
```
/home/yourusername/rekapabsensi/venv
```

### WSGI configuration file:
Edit `/var/www/yourusername_pythonanywhere_com_wsgi.py`:

```python
import os
import sys

# Add your project directory to sys.path
path = '/home/yourusername/rekapabsensi'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'sipa_yaumi.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

## Step 8: Configure Static Files

In the Web tab, add static file mappings:

### URL: `/static/`
### Directory: `/home/yourusername/rekapabsensi/staticfiles/`

### URL: `/media/`
### Directory: `/home/yourusername/rekapabsensi/media/`

## Step 9: Test the Application

1. Click "Reload" in the Web tab
2. Visit your app at `https://yourusername.pythonanywhere.com`
3. Test login with your superuser credentials
4. Verify all functionality works correctly

## Step 10: Ongoing Maintenance

### Updating the Application

```bash
# Pull latest changes
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Reload the web app from PythonAnywhere dashboard
```

### Database Backup

```bash
# Create backup
python manage.py dumpdata > backup_$(date +%Y%m%d_%H%M%S).json

# Restore from backup (if needed)
python manage.py loaddata backup_filename.json
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Check that your virtual environment is properly configured in the WSGI file
2. **Static Files Not Loading**: Verify static file mappings in the Web tab
3. **Database Errors**: Ensure migrations have been run and database permissions are correct
4. **Environment Variables**: Check that `.env` file exists and contains correct values

### Checking Logs

- Error logs: Available in PythonAnywhere Web tab → Log files
- Server logs: Check `/var/log/yourusername.pythonanywhere.com.server.log`
- Error logs: Check `/var/log/yourusername.pythonanywhere.com.error.log`

### Performance Tips

1. Use PythonAnywhere's built-in caching
2. Optimize database queries
3. Compress static files
4. Use CDN for static assets (paid accounts)

## Security Considerations

1. Always use HTTPS in production
2. Keep SECRET_KEY secure and unique
3. Set DEBUG=False in production
4. Regularly update dependencies
5. Use strong passwords for admin accounts

## Support

- PythonAnywhere Help: https://help.pythonanywhere.com/
- Django Documentation: https://docs.djangoproject.com/
- Project Issues: Create an issue in your GitHub repository