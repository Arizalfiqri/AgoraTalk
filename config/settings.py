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
    # Header & Branding
    "site_title": "AgoraTalk",
    "site_header": "Admin AgoraTa",
    "site_brand": "AgoraTalk",
    # "site_logo": "images/logo.png",
    "site_icon": "images/logo_agora",
    "welcome_sign": "Selamat datang di Panel Admin AgoraTalk",
    "copyright": "AgoraTalk",
    
    # Search
    "search_model": ["forum.Thread", "forum.User"],
    
    # Navigation
    "topmenu_links": [
        {"name": "Lihat Site", "url": "/", "permissions": ["auth.view_user"], "new_window": True},
        {"name": "Dashboard", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"model": "forum.Thread"},
        {"model": "forum.Report"},
    ],
    
    # Sidebar
    "show_sidebar": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "hide_models": [],
    
    # UI Configuration
    "order_with_respect_to": ["forum", "auth"],
    "show_ui_builder": False,
    
    # Theme & Layout
    "theme": "flatly",  # Professional and clean theme
    "dark_mode_theme": "darkly",
    

    
    # Icons (Font Awesome)
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "forum.User": "fas fa-user-graduate",
        "forum.Thread": "fas fa-comments",
        "forum.Comment": "fas fa-comment-alt",
        "forum.Category": "fas fa-folder-open",
        "forum.Vote": "fas fa-thumbs-up",
        "forum.Bookmark": "fas fa-bookmark",
        "forum.Notification": "fas fa-bell",
        "forum.Report": "fas fa-flag",
    },
    
    # Related modal
    "related_modal_active": False,
    
    # UI Tweaks
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "forum.user": "collapsible",
        "forum.thread": "horizontal_tabs"
    },
    
    # Language
    "language_chooser": False,

}


JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    },
    "actions_sticky_top": False
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'forum.middleware.UserActivityMiddleware',  # Tambahkan ini
    # 'forum.middleware.SessionSeparationMiddleware',
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
    }
}

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
DEFAULT_FROM_EMAIL = 'AgoraTalk <fikriganteng238@gmail.com>'


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

