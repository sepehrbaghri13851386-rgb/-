"""
Settings for the "restoran_asli" project (DeliTaste template).
"""

import os
from pathlib import Path
import dj_database_url

# BASE_DIR = the folder that contains manage.py, templates/ and static/
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# SECURITY & ENVIRONMENT VARIABLES
# ---------------------------------------------------------------------------
# اگر در رندر باشیم، متغیرهای محیطی وجود دارند. اگر لوکال باشیم، مقادیر پیش‌فرض استفاده می‌شوند.
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-key-change-me')

# تشخیص خودکار محیط: اگر متغیر RENDER وجود داشت یعنی روی سرور هستیم
IS_RENDER = 'RENDER' in os.environ

# اگر روی رندر باشیم، DEBUG باید False باشد. در غیر این صورت True
DEBUG = os.environ.get('DEBUG', 'False' if IS_RENDER else 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

CSRF_TRUSTED_ORIGINS = ['https://*.onrender.com']

# ---------------------------------------------------------------------------
# APPLICATIONS & MIDDLEWARE
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'cloudinary_storage',              # قبل از staticfiles
    'django.contrib.staticfiles',
    'cloudinary',                      # بعد از staticfiles
    'django.contrib.humanize',
    'ghaza_app',
    'GOZIYAT_APP',
    'nazerat_app',
    'blog_app',
    'restoran_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'restoran_asli.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],      # <- all the .html pages live here
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

WSGI_APPLICATION = 'restoran_asli.wsgi.application'

# ---------------------------------------------------------------------------
# DATABASE (SMART SWITCH)
# ---------------------------------------------------------------------------
# منطق کار: 
# اگر روی رندر باشیم (RENDER env وجود دارد) و لینک دیتابیس (DATABASE_URL) ست شده باشد،
# به دیتابیس اصلی وصل می‌شود. در غیر این صورت (روی سیستم شما)، از SQLite استفاده می‌کند.
# ---------------------------------------------------------------------------
if IS_RENDER and os.environ.get('DATABASE_URL'):
    # محیط پروداکشن (Render)
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # محیط لوکال (سیستم شخصی شما)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db_local.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# STATIC & MEDIA FILES
# ---------------------------------------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
}

STORAGES = {
    "default": {"BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'