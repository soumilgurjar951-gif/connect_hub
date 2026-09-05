"""
Django settings for connect_hub project.
ConnectHub - Instagram + Twitter ka simple version

Hinglish Concept: settings.py = Ghar ka main switchboard.
Yahan se sab control hota hai - kaunse apps chalenge, database kahan hai,
static/media files kahan save honge.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# .env file load karo (production me Railway/Render se env vars ayenge)
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ============ SECURITY ============
# Secret key .env se lo, nahi mila to dev wala use karo
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-q=#i^1%w7a2w2gg$z-3=ii$!r29$10)u1vv-^rri-4h#zkm%+_')

# DEBUG = True -> local me error dikhega, production me False
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',')
# testserver Django test Client ke liye hamesha allow karo
if 'testserver' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('testserver')

# ============ APPS ============
# Django ke default apps + apne custom apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps (pip install se ayenge)
    'rest_framework',      # API ke liye
    'corsheaders',         # Frontend alag domain pe ho to CORS handle

    # Apne apps - yahan saare features rahenge
    'accounts',            # Profile + Follow system
    'posts',               # Post + PostImage + Like + Comment
    'chat',                # Direct Messaging (1-to-1)
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Static files production me serve karne ke liye
    'corsheaders.middleware.CorsMiddleware',       # CORS sabse upar hona chahiye
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'connect_hub.urls'

# ============ TEMPLATES ============
# DIRS me BASE_DIR / 'templates' matlab global templates folder
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',  # media URL templates me use karne ke liye
            ],
        },
    },
]

WSGI_APPLICATION = 'connect_hub.wsgi.application'

# Channels ke liye ASGI (MVP me polling use karenge, baad me WebSocket)
# ASGI_APPLICATION = 'connect_hub.asgi.application'

# ============ DATABASE ============
# Local me SQLite (file-based, setup easy), Production me PostgreSQL
# DATABASE_URL env var se PostgreSQL auto-detect (Railway/Render deta hai)
import dj_database_url

if os.getenv('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.parse(os.getenv('DATABASE_URL'))
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ============ PASSWORD VALIDATORS ============
# Hinglish: MVP ke liye easy rakha - username == password allow karna hai to Similarity validator hata diya
# Pehle UserAttributeSimilarityValidator rok raha tha ("password too similar to username")
AUTH_PASSWORD_VALIDATORS = [
    # {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},  # HATA DIYA - ab username==password allowed
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 6}},
    # Common/Numeric bhi hata sakte ho agar aur easy chahiye, abhi rakha hai
    # {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    # {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============ INTERNATIONALIZATION ============
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'  # India ka timezone, UTC nahi
USE_I18N = True
USE_TZ = True

# ============ STATIC FILES (CSS, JS) ============
# Hinglish: static = jo kabhi change nahi hota (CSS/JS/logo)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']  # tumhare CSS/JS yahan rahenge
STATIC_ROOT = BASE_DIR / 'staticfiles'    # production me collectstatic yahan dalta hai
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ============ MEDIA FILES (User uploads) ============
# Hinglish: media = user jo upload kare (avatar, post images)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ============ AUTH SETTINGS ============
LOGIN_URL = '/accounts/login/'          # @login_required pe yahan redirect
LOGIN_REDIRECT_URL = '/'                # login ke baad kahan jana hai
LOGOUT_REDIRECT_URL = '/accounts/login/'

# ============ DJANGO REST FRAMEWORK ============
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,  # Feed me 20 posts per page (requirement)
}

# ============ CORS (API ke liye) ============
# Hinglish: React Vite (localhost:5173) se Django (127.0.0.1:8000) pe session cookie bhejne ke liye credentials True chahiye.
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Dev me sab allow, prod me specific domain
CORS_ALLOW_CREDENTIALS = True
# Vite proxy same-origin banata hai (/api -> Django), phir bhi direct call ke liye trusted origins rakho
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000').split(',')
# Production me: CORS_ALLOWED_ORIGINS = ['https://yourdomain.com']

# ============ FILE UPLOAD LIMITS ============
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# ============ PROD SECURITY (Real-world launch) ============
if not DEBUG:
    # Hinglish: Public pe jaate hi HTTPS + HSTS + secure cookies must. Railway/Render auto HTTPS dete hain.
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True') == 'True'  # set False if behind proxy without HTTPS
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    # Trust proxy (Railway/Render)
    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
else:
    # Dev me loose rakho
    SECURE_SSL_REDIRECT = False

# ============ STORAGE: Local dev vs S3/R2 prod (public launch) ============
# Env set karo to S3/R2 pe media jayega, warna local MEDIA_ROOT
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
if AWS_STORAGE_BUCKET_NAME:
    # pip install django-storages boto3
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'auto')
    AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')  # R2: https://<id>.r2.cloudflarestorage.com
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
    AWS_DEFAULT_ACL = 'public-read'
    AWS_QUERYSTRING_AUTH = False
    # Media S3 pe, static WhiteNoise pe rahega (simple)
    from storages.backends.s3boto3 import S3Boto3Storage
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    # Optional: STATIC on S3 (agar chaho to enable)
    # STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'

# ============ LOGGING (Real-world) ============
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'INFO'},
}

# ============ DEFAULT AUTO FIELD ============
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============ EMAIL (MVP me verification nahi chahiye, isliye console backend) ============
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
# Prod me: EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend + EMAIL_HOST etc

# ============ SESSION ============
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 1 week tak login rahega
# Public me session same-site lax for 3rd party safe
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False
