# Document Management System - Installation Guide

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)
- Git (optional, for cloning)

## 🚀 Quick Start Installation

### Step 1: Create Project Structure

```bash
# Create main project directory
mkdir dms_project
cd dms_project

# Create Django project
django-admin startproject config .

# Create documents app
python manage.py startapp documents
```

### Step 2: Copy Project Files

Copy all the provided files to their respective locations:
- `documents/models.py` → Your models
- `documents/views.py` → Your views
- `documents/urls.py` → Your URL configurations
- `documents/forms.py` → Your forms
- `documents/admin.py` → Admin configuration
- `documents/api_views.py` → API views (optional)
- `documents/api_urls.py` → API URLs (optional)

### Step 3: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 4: Install Dependencies

```bash
# Install basic requirements
pip install django pillow

# Or install from requirements.txt
pip install -r requirements.txt
```

### Step 5: Configure Settings

Edit `config/settings.py`:

```python
# Add documents app to INSTALLED_APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'documents',  # Add this
]

# Custom User Model (Add at bottom of file)
AUTH_USER_MODEL = 'documents.User'

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB

# Login URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'home'
```

### Step 6: Configure URLs

Edit `config/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('documents.urls')),
    # Optional: API endpoints
    # path('api/', include('documents.api_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

### Step 7: Create Required Directories

```bash
# Create media directories
mkdir -p media/documents
mkdir -p media/avatars
mkdir -p media/document_versions

# Create static directories
mkdir -p static/css
mkdir -p static/js
mkdir -p static/images

# Create template directories
mkdir -p documents/templates/documents
mkdir -p documents/templates/documents/auth
mkdir -p documents/templates/documents/admin

# Create management command directory
mkdir -p documents/management/commands
```

### Step 8: Initialize Database

```bash
# Create migrations
python manage.py makemigrations documents

# Apply migrations
python manage.py migrate
```

### Step 9: Initialize System with Default Data

```bash
# Run initialization command
python manage.py initialize_dms
```

This will create:
- Default roles (Viewer, Contributor, Editor, Manager, Administrator)
- Default categories (General, Financial, HR, Legal, etc.)
- Demo admin user (username: admin, password: admin123)

### Step 10: Create Superuser (Optional)

```bash
# If you want to create your own admin user instead of using the demo one
python manage.py createsuperuser
```

Follow the prompts to create your admin account.

### Step 11: Create Static Files Directory

```bash
# Collect static files
python manage.py collectstatic --noinput
```

### Step 12: Run Development Server

```bash
python manage.py runserver
```

## 🌐 Access the Application

- **Main Application**: http://localhost:8000/
- **Admin Panel**: http://localhost:8000/admin/
- **API** (if enabled): http://localhost:8000/api/

## 🔐 Default Login Credentials

If you used the initialization command:
- **Username**: admin
- **Password**: admin123

⚠️ **IMPORTANT**: Change this password immediately after first login!

## 📁 Project Structure After Installation

```
dms_project/
├── config/                      # Django project settings
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── documents/                   # Main application
│   ├── migrations/             # Database migrations
│   ├── management/             # Management commands
│   │   └── commands/
│   │       └── initialize_dms.py
│   ├── templates/              # HTML templates
│   │   └── documents/
│   │       ├── auth/          # Authentication templates
│   │       ├── admin/         # Admin templates
│   │       └── ...
│   ├── __init__.py
│   ├── admin.py               # Admin configuration
│   ├── api_urls.py            # API URL routing
│   ├── api_views.py           # API views
│   ├── apps.py
│   ├── forms.py               # Form definitions
│   ├── models.py              # Database models
│   ├── tests.py
│   ├── urls.py                # URL routing
│   └── views.py               # View functions
├── media/                      # User uploaded files
│   ├── documents/             # Document files
│   ├── avatars/               # User avatars
│   └── document_versions/     # Version files
├── static/                     # Static files
│   ├── css/
│   ├── js/
│   └── images/
├── staticfiles/               # Collected static files
├── venv/                      # Virtual environment
├── manage.py
├── requirements.txt
├── README.md
└── INSTALLATION_GUIDE.md
```

## 🧪 Testing the Installation

### 1. Test Admin Access
```bash
# Navigate to admin panel
http://localhost:8000/admin/

# Login with your credentials
# Verify you can see all models
```

### 2. Test User Registration
```bash
# Go to registration page
http://localhost:8000/register/

# Create a new user account
# Login and access dashboard
```

### 3. Test Document Upload
```bash
# Login to the application
# Click "Create Document"
# Upload a test file
# Verify it appears in document list
```

## 🐛 Troubleshooting

### Common Issues

**1. Module not found errors**
```bash
# Make sure you're in the virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**2. Database errors**
```bash
# Delete database and start fresh
rm db.sqlite3
python manage.py migrate
python manage.py initialize_dms
```

**3. Media files not serving**
```bash
# Make sure DEBUG=True in settings.py
# Check MEDIA_URL and MEDIA_ROOT settings
# Verify urls.py includes static file serving
```

**4. Permission denied errors**
```bash
# On Unix-like systems, ensure proper permissions
chmod -R 755 media/
chmod -R 755 static/
```

**5. Import errors**
```bash
# Ensure AUTH_USER_MODEL is set in settings.py BEFORE migrations
AUTH_USER_MODEL = 'documents.User'
```

## 🔧 Additional Configuration

### PostgreSQL Database (Production)

```python
# In settings.py, replace DATABASES with:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'dms_db',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Email Configuration

```python
# In settings.py, add:
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
```

### Production Settings

```python
# In settings.py for production:
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

## 📚 Next Steps

1. **Customize Templates**: Create HTML templates in `documents/templates/`
2. **Add Styling**: Add CSS files to `static/css/`
3. **Configure Email**: Set up email notifications
4. **Set Up Production**: Configure production server (Gunicorn, Nginx)
5. **Enable API**: Uncomment API URLs for REST API access
6. **Add Tests**: Write unit tests in `documents/tests.py`

## 🆘 Getting Help

- Check the README.md for feature documentation
- Review SETTINGS_GUIDE.md for configuration options
- Check Django documentation: https://docs.djangoproject.com/
- Create an issue in the repository

## ✅ Verification Checklist

- [ ] Virtual environment created and activated
- [ ] All dependencies installed
- [ ] Settings configured correctly
- [ ] Database migrations applied
- [ ] Default data initialized
- [ ] Admin user created
- [ ] Static files collected
- [ ] Server runs without errors
- [ ] Can access admin panel
- [ ] Can register new users
- [ ] Can upload documents
- [ ] Media files are served correctly

## 🎉 Congratulations!

Your Document Management System is now installed and ready to use!