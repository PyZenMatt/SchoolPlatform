from pathlib import Path
import os
from datetime import timedelta
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Carica il file .env che deve stare nella root del progetto (stesso livello di manage.py)
load_dotenv(BASE_DIR / '.env')

BASE_DIR = Path(__file__).resolve().parent.parent
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Allowed hosts
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver'] if DEBUG else ['localhost', '127.0.0.1', 'your-domain.com']


# App
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # REST & JWT
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',

    # Utility
    'corsheaders',
    'drf_spectacular',
    'modelcluster',
    'taggit',

    # App personalizzate
    'authentication',
    'core.apps.CoreConfig',
    'users',
    'courses',
    'rewards',
    'notifications',
    'blockchain',
]

# Debug toolbar (solo in development)
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar',
                       'django_extensions']

# Middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.AutoJWTFromSessionMiddleware',
    'core.middleware.APITimingMiddleware',  # Performance monitoring
    'core.middleware.GlobalErrorHandlingMiddleware',  # Global error handling
]

# Debug toolbar middleware
if DEBUG:
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1', 'localhost']

# URL
ROOT_URLCONF = 'schoolplatform.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'schoolplatform.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,  # Reduced from 30 for faster response
            'check_same_thread': False,
        }
    }
}

# Database connection pooling and optimization for development
if DEBUG:
    DATABASES['default']['CONN_MAX_AGE'] = 60  # Connection pooling for 60 seconds
    DATABASES['default']['CONN_HEALTH_CHECKS'] = True  # Health checks for connections

# Password
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# JWT Configuration
SIMPLE_JWT = {
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'TOKEN_OBTAIN_SERIALIZER': 'authentication.serializers.CustomTokenObtainPairSerializer',
}

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Auth user model
AUTH_USER_MODEL = 'users.User'

# Static & Media
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Sessioni
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_COOKIE_AGE = 3600
SESSION_COOKIE_HTTPONLY = True

# CORS
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001", 
    "http://127.0.0.1:3001",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8001",
    "http://127.0.0.1:8001"
]

# Configurazioni CORS aggiuntive per il debug
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Solo in sviluppo
CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'cache-control',
    'pragma',
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Preflight cache per migliorare le performance
CORS_PREFLIGHT_MAX_AGE = 86400

# Login/Logout redirect
LOGIN_REDIRECT_URL = '/app/dashboard/default'
LOGOUT_REDIRECT_URL = '/login/'

# Email (solo console in dev)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'no-reply@teocoin.io'
DEBUG_EMAIL_VERIFICATION = True

# Altri
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Media files (uploads)
import os
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Blockchain Configuration
POLYGON_AMOY_RPC_URL = os.getenv('POLYGON_AMOY_RPC_URL', 'https://rpc-amoy.polygon.technology/')
TEOCOIN_CONTRACT_ADDRESS = os.getenv('TEOCOIN_CONTRACT_ADDRESS', '0x20D6656A31297ab3b8A87291Ed562D4228Be9ff8')
ADMIN_PRIVATE_KEY = os.getenv('ADMIN_PRIVATE_KEY')
ADMIN_WALLET_ADDRESS = os.getenv('ADMIN_WALLET_ADDRESS')

# Reward Pool Configuration 
REWARD_POOL_ADDRESS = os.getenv('REWARD_POOL_ADDRESS', '0x17051AB7603B0F7263BC86bF1b0ce137EFfdEcc1')
REWARD_POOL_PRIVATE_KEY = os.getenv('REWARD_POOL_PRIVATE_KEY', os.getenv('ADMIN_PRIVATE_KEY'))

# =====================================
# 🚀 PERFORMANCE OPTIMIZATION CONFIG
# =====================================

# Redis Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 20,
            },
        },
        'KEY_PREFIX': 'schoolplatform',
    }
}

# Session cache
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Celery Configuration
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Rome'

# Sentry Configuration (only in production)
if not DEBUG:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(),
            CeleryIntegration()
        ],
        traces_sample_rate=0.1,
        send_default_pii=True,
        environment=ENVIRONMENT,
    )

# Database connection optimizations
if 'sqlite' not in DATABASES['default']['ENGINE']:
    DATABASES['default']['CONN_MAX_AGE'] = 600
    DATABASES['default']['OPTIONS'] = {
        'MAX_CONNS': 20,
    }

# API Response Time Logging
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
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'api_performance.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'api_performance': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# File Upload Settings - Support for larger video files
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB - files larger than this will be saved to disk
DATA_UPLOAD_MAX_MEMORY_SIZE = 250 * 1024 * 1024  # 250MB - maximum total upload size
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# Media file serving timeout for large files
FILE_UPLOAD_TEMP_DIR = None  # Use system default temp directory
