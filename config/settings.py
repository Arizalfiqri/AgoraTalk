"""
Django settings for portal_komunitas_forum_mahasiswa project.
Enhanced version with professional features.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files (User uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-f%fhghnck$_mipbnr10#00x(aw+#juwrg0bac+-)i&hlkoaud4'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",  # For better date/number formatting
    "forum",
]

# Jazzmin admin customization
JAZZMIN_SETTINGS = {
    "site_logo": "images/logo.png",
    "site_icon": "images/favicon.ico",
    "site_title": "Portal Forum Mahasiswa",
    "site_header": "Admin Forum Kampus",
    "site_brand": "ForumKampus",
    "welcome_sign": "Selamat datang di Panel Admin Forum Kampus!",
    "copyright": "Universitas Muhammadiyah",
    "search_model": "forum.Thread",

    # Menu customization
    "topmenu_links": [
        {"name": "Beranda", "url": "/", "permissions": ["auth.view_user"]},
        {"model": "forum.Thread"},
        {"model": "forum.Comment"},
        {"model": "forum.Category"},
    ],

    "show_sidebar": True,
    "navigation_expanded": True,

    # Theme
    "theme": "darkly",
    
    # Icons
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "forum.Thread": "fas fa-comments",
        "forum.Comment": "fas fa-comment",
        "forum.Category": "fas fa-folder",
        "forum.Vote": "fas fa-thumbs-up",
        "forum.Bookmark": "fas fa-bookmark",
        "forum.Notification": "fas fa-bell",
    },
    
    # Custom styling
    "custom_css": "admin/custom.css",
    "custom_js": "admin/custom.js",
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'forum.middleware.AdminUserMiddleware',
    'forum.middleware.SessionSeparationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',  # For media files
            ],
        },  
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/
LANGUAGE_CODE = 'id'  # Indonesian
TIME_ZONE = 'Asia/Jakarta'
USE_I18N = True
USE_TZ = True

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login/Logout URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Messages framework
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Cache (for better performance)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

ADMIN_SITE_HEADER = 'Portal Forum Mahasiswa'
ADMIN_SITE_TITLE = 'Forum Admin'
ADMIN_INDEX_TITLE = 'Dashboard Administrasi'

# Chart.js untuk analytics (tambahkan ke JAZZMIN_SETTINGS)
JAZZMIN_SETTINGS.update({
    "custom_links": {
        "forum": [{
            "name": "Analytics Dashboard",
            "url": "admin:analytics",
            "icon": "fas fa-chart-bar",
            "permissions": ["forum.view_thread"]
        }]
    }
})

# Login/Logout redirects
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Session settings
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'admin_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'admin_db.sqlite3',
    }
}

# Database router
DATABASE_ROUTERS = ['forum.database_router.DatabaseRouter']

# Custom User Model
AUTH_USER_MODEL = 'forum.User'

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Gmail SMTP Configuration (recommended for production)
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'fikriganteng238@gmail.com'  # Ganti dengan email Anda
EMAIL_HOST_PASSWORD = 'cwju ziol isip srez'  # Ganti dengan App Password Gmail
DEFAULT_FROM_EMAIL = 'Forum Kampus <fikriganteng238@gmail.com>'

# Alternative: Console Backend for Development/Testing
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Session Configuration (untuk menyimpan kode verifikasi)
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 3600  # 1 jam
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Admin session settings
ADMIN_SESSION_COOKIE_NAME = 'admin_sessionid'
ADMIN_SESSION_COOKIE_AGE = 7200  # 2 jam untuk admin

# Security Settings
SECURE_SSL_REDIRECT = False  # Set to True in production with HTTPS
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
CSRF_COOKIE_SECURE = False  # Set to True in production with HTTPS


# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'forum.views.AdminAuthenticationBackend',
    'forum.views.UserAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Password Validation
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

# Logging Configuration (untuk debugging email)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.core.mail': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

