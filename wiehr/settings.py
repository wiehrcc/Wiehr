
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


SECRET_KEY = os.getenv("SECRET_KEY")
ENV = os.getenv("ENV", "DEV")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

if ENV == 'PROD':
    ALLOWED_HOSTS = ['127.0.0.1', '18.199.60.75', 'wiehr.cc', 'www.wiehr.cc']
else:
    ALLOWED_HOSTS = ['*']


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'compressor',
    'ckeditor',
    'htmlmin',
    
    'web',
]

MIDDLEWARE = [
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'wiehr.cache_middleware.StaticFilesCacheMiddleware',
    # WhiteNoise serves /static/ straight from STATIC_ROOT, which means every
    # edit needs a collectstatic before it shows up. Only mount it on PROD;
    # locally the staticfiles finders serve the source files live (see urls.py).
    *(['whitenoise.middleware.WhiteNoiseMiddleware'] if ENV == 'PROD' else []),
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'htmlmin.middleware.HtmlMinifyMiddleware'
]

ROOT_URLCONF = 'wiehr.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates/')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'wiehr.wsgi.application'


if ENV == 'PROD':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db_prod.sqlite3',
            'OPTIONS': {
                'timeout': 20,
            }
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'OPTIONS': {
                'timeout': 20,
            }
        }
    }


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


TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
LANGUAGE_CODE = 'en-us'

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

DATE_FORMAT = 'd.m.Y'
DATE_INPUT_FORMATS = ('%d.%m.%Y', )

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
if ENV != 'PROD':
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, 'web', 'static'),
    ]
else:
    STATICFILES_DIRS = []

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "false").lower() == "true"
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "30"))
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", f"Wiehr <{EMAIL_HOST_USER or 'no-reply@wiehr.cc'}>")
TEAM_EMAIL_BATCH_SIZE = int(os.getenv("TEAM_EMAIL_BATCH_SIZE", "50"))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

if ENV == 'PROD':
    SITE_URL = 'https://wiehr.cc/'
    SITE_URL_NODASHED = 'https://wiehr.cc'

    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True

    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_HSTS_SECONDS = 31536000
    
    CSP_DEFAULT_SRC = ["'self'"]
    CSP_SCRIPT_SRC = ["'self'", "'unsafe-inline'", "https://www.googletagmanager.com"]
    CSP_STYLE_SRC = ["'self'", "'unsafe-inline'"]
    CSP_IMG_SRC = ["'self'", "data:", "https:"]
    CSP_FONT_SRC = ["'self'", "data:"]
    CSP_CONNECT_SRC = ["'self'", "https://www.google-analytics.com"]
    CSP_FRAME_ANCESTORS = ["'none'"]
else:
    SITE_URL = 'http://127.0.0.1:8000/'
    SITE_URL_NODASHED = 'http://127.0.0.1:8000'

MAXIMUM_URL_CHARS = 3

SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

if ENV == 'PROD':
    COMPRESS_ENABLED = True
    COMPRESS_OFFLINE = True
    COMPRESS_ROOT = STATIC_ROOT
    COMPRESS_URL = '/static/'
    COMPRESS_CSS_HASHING_METHOD = 'content'
    COMPRESS_FILTERS = {
        'css':[
            'compressor.filters.css_default.CssAbsoluteFilter',
            'compressor.filters.cssmin.rCSSMinFilter',
        ],
        'js':[
            'compressor.filters.jsmin.JSMinFilter',
        ]
    }
    HTML_MINIFY = True
    KEEP_COMMENTS_ON_MINIFYING = False
else:
    COMPRESS_ENABLED = False
    HTML_MINIFY = True

MEDIA_FULL = f"{SITE_URL}{MEDIA_URL}"

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['|', 'Bold', 'Italic', 'Underline', 'Blockquote', 'Strike'],
            ['NumberedList', 'BulletedList', '|', 'Outdent', 'Indent', '|', 'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['Link', 'Unlink'],
            ['RemoveFormat', '-', 'Preview', 'Maximize']
        ],
    },
}

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

WHITENOISE_MAX_AGE = 31536000

if ENV == 'PROD':
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }
    
    CACHE_MIDDLEWARE_ALIAS = 'default'
    CACHE_MIDDLEWARE_SECONDS = 600
    CACHE_MIDDLEWARE_KEY_PREFIX = ''