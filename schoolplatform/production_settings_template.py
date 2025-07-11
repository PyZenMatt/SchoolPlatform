
# Production Settings Template
# Copy this to production_settings.py and configure for your deployment

import os
from .settings import *

# Security Settings
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY', 'CHANGE_THIS_IN_PRODUCTION')
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# HTTPS Security
SECURE_SSL_REDIRECT = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookies
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True

# Database (PostgreSQL recommended)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Blockchain Configuration
POLYGON_RPC_URL = os.environ.get('POLYGON_RPC_URL')
TEOCOIN_CONTRACT_ADDRESS = os.environ.get('TEOCOIN_CONTRACT_ADDRESS')
REWARD_POOL_ADDRESS = os.environ.get('REWARD_POOL_ADDRESS')
GAS_TREASURY_PRIVATE_KEY = os.environ.get('GAS_TREASURY_PRIVATE_KEY')

# Static files (configure for your CDN/storage)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/schoolplatform/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
