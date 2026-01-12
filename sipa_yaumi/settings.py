"""
Django settings for sipa_yaumi project.
Enterprise-grade configuration with proper security and performance settings.
"""

from pathlib import Path
import os
from decouple import config, Csv
import logging.config
from django.templatetags.static import static
from django.urls import reverse_lazy

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,testserver', cast=Csv())

# Application definition
DJANGO_APPS = [
    'unfold',  # Must be before django.contrib.admin
    'unfold.contrib.filters',  # Optional: Unfold filters
    'unfold.contrib.forms',  # Optional: Unfold forms
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

THIRD_PARTY_APPS = [
    # Add other third-party apps here
]

LOCAL_APPS = [
    'attendance',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'attendance.middleware.CurrentUserMiddleware',  # Must be after AuthenticationMiddleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'attendance.middleware.AuditMiddleware',  # Custom audit middleware
]

ROOT_URLCONF = 'sipa_yaumi.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'attendance.context_processors.app_context',  # Custom context processor
            ],
        },
    },
]

WSGI_APPLICATION = 'sipa_yaumi.wsgi.application'

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.sqlite3'),
        'NAME': config('DB_NAME', default=BASE_DIR / 'db.sqlite3'),
        'USER': config('DB_USER', default=''),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default=''),
        'PORT': config('DB_PORT', default=''),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        } if config('DB_ENGINE', default='').endswith('mysql') else {},
    }
}

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
    } if config('USE_REDIS', default=False, cast=bool) else {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'id'
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/admin/login/'

# Session configuration
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_SAVE_EVERY_REQUEST = True

# CSRF configuration
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True

# Security settings
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'attendance': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# Application-specific settings
SIPA_YAUMI = {
    'SCHOOL_NAME': 'PESANTREN YAUMI YOGYAKARTA',
    'APP_NAME': 'SIPA Beta ',
    'APP_SUBTITLE': 'Sistem Informasi Presensi Pesantren Yaumi',
    'APP_INITIALS': 'SY',
    'VERSION': '2.0.0',
    'PAGINATION_SIZE': 20,
    'REPORT_PAGINATION_SIZE': 50,
    'MAX_EXPORT_RECORDS': 10000,
    'ATTENDANCE_CUTOFF_TIME': '23:59',  # Latest time to record attendance
    'BACKUP_RETENTION_DAYS': 30,
}

# Email configuration (for notifications)
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@sipayaumi.com')

# Performance settings
if not DEBUG:
    # Enable template caching
    TEMPLATES[0]['OPTIONS']['loaders'] = [
        ('django.template.loaders.cached.Loader', [
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        ]),
    ]

# Custom user model (if needed in future)
# AUTH_USER_MODEL = 'attendance.User'

# Unfold settings - Fixed configuration
UNFOLD = {
    "SITE_TITLE": "SIPA Beta ",
    "SITE_HEADER": "SIPA Beta  Administration", 
    "SITE_URL": "/admin/",
    "SITE_SYMBOL": "📚",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "STYLES": [
        lambda request: static("admin/css/custom_unfold.css"),
        lambda request: static("admin/css/dashboard.css"),
    ],
    "SCRIPTS": [
        lambda request: static("admin/js/custom_unfold.js"),
    ],
    "COLORS": {
        "primary": {
            "50": "240 249 255",
            "100": "224 242 254", 
            "200": "186 230 253",
            "300": "125 211 252",
            "400": "56 189 248",
            "500": "14 165 233",
            "600": "2 132 199",
            "700": "3 105 161",
            "800": "7 89 133",
            "900": "12 74 110",
            "950": "8 47 73"
        }
    },
    "SIDEBAR": {
        "show_search": False,  # Disable to avoid URL issues
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Dashboard",
                "separator": True,
                "items": [
                    {
                        "title": "Dashboard Utama",
                        "icon": "dashboard",
                        "link": lambda request: "/admin/",
                    },
                ],
            },
            {
                "title": "Manajemen Siswa",
                "separator": True,
                "items": [
                    {
                        "title": "Academic Levels",
                        "icon": "school",
                        "link": lambda request: reverse_lazy("admin:attendance_academiclevel_changelist"),
                    },
                    {
                        "title": "Classrooms", 
                        "icon": "meeting_room",
                        "link": lambda request: reverse_lazy("admin:attendance_classroom_changelist"),
                    },
                    {
                        "title": "Students",
                        "icon": "people",
                        "link": lambda request: reverse_lazy("admin:attendance_student_changelist"),
                    },
                ],
            },
            {
                "title": "Manajemen Absensi",
                "separator": True,
                "items": [
                    {
                        "title": "Ambil Absensi",
                        "icon": "check_circle",
                        "link": lambda request: "/attendance/",
                    },
                    {
                        "title": "Attendance Records",
                        "icon": "assignment",
                        "link": lambda request: reverse_lazy("admin:attendance_attendancerecord_changelist"),
                    },
                    {
                        "title": "Attendance Summary",
                        "icon": "analytics",
                        "link": lambda request: reverse_lazy("admin:attendance_attendancesummary_changelist"),
                    },
                ],
            },
            {
                "title": "Sistem & Audit",
                "separator": True,
                "items": [
                    {
                        "title": "Audit Logs",
                        "icon": "history",
                        "link": lambda request: reverse_lazy("admin:attendance_auditlog_changelist"),
                    },
                    {
                        "title": "Users",
                        "icon": "person",
                        "link": lambda request: reverse_lazy("admin:auth_user_changelist"),
                    },
                    {
                        "title": "Groups",
                        "icon": "group",
                        "link": lambda request: reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
        ],
    },
}