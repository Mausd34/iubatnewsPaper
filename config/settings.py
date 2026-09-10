"""
Django settings for the IUBAT Campus Newspaper Portal.

Week 1 deliverable: static/media/templates/auth/database configuration.
Reads environment-specific values from a local `.env` file (python-decouple).
"""

from pathlib import Path

import dj_database_url
from decouple import Csv, config

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Core security
# ---------------------------------------------------------------------------
SECRET_KEY = config(
    "SECRET_KEY",
    default="django-insecure-dev-key-only-for-local-development-change-me",
)
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv()
)
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="http://localhost:8000,http://127.0.0.1:8000",
    cast=Csv(),
)

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.sites",
    "django.contrib.humanize",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",
    "corsheaders",
    "tinymce",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.articles",
    "apps.dashboard",
    "apps.newsletter",
    "apps.core",
    "apps.api",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # static files in production
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
SITE_ID = 1

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.branding",
                "apps.articles.context_processors.nav_categories",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Database — PostgreSQL in production (DATABASE_URL), SQLite in development
# ---------------------------------------------------------------------------
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

# ---------------------------------------------------------------------------
# Auth — custom user model
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.CustomUser"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation."
             "UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation."
             "MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation."
             "CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation."
             "NumericPasswordValidator"},
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "core:home"
LOGOUT_REDIRECT_URL = "core:home"

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Dhaka"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static & media
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
        if not DEBUG
        else "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# ---------------------------------------------------------------------------
# Default primary key field & email
# ---------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = config(
    "DEFAULT_FROM_EMAIL", default="IUBAT News <news@iubatnews.edu>"
)

# ---------------------------------------------------------------------------
# Caching (local-memory in dev; swap for memcached/redis in production)
# ---------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "iubat-news-cache",
    }
}

# ---------------------------------------------------------------------------
# Django REST Framework + JWT
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS":
        "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 12,
}

from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
}

# CORS (lock this down in production)
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:3000,http://localhost:8000",
    cast=Csv(),
)

# ---------------------------------------------------------------------------
# TinyMCE (rich-text article body)
# ---------------------------------------------------------------------------
TINYMCE_DEFAULT_CONFIG = {
    "height": "480",
    "menubar": "file edit view insert format tools table help",
    "plugins": (
        "advlist autolink lists link image charmap preview anchor "
        "searchreplace visualblocks code fullscreen insertdatetime "
        "media table help wordcount"
    ),
    "toolbar": (
        "undo redo | blocks | bold italic underline | "
        "alignleft aligncenter alignright alignjustify | "
        "bullist numlist outdent indent | link image media | "
        "removeformat code fullscreen"
    ),
    "image_advtab": True,
}

# ---------------------------------------------------------------------------
# IUBAT branding
# ---------------------------------------------------------------------------
IUBAT_BRAND = {
    "NAME": "IUBAT Campus News",
    "FULL_NAME": "International University of Business Agriculture and "
                 "Technology",
    "PRIMARY_COLOR": "#006400",  # IUBAT green
    "ACCENT_COLOR": "#008000",
    "TAGLINE": "The independent student voice of IUBAT",
}

# Pagination
ARTICLES_PER_PAGE = 9
TRENDING_WINDOW_DAYS = 7

# Cloudinary (optional) — set CLOUDINARY_CLOUD_NAME in .env to enable
CLOUDINARY_CLOUD_NAME = config("CLOUDINARY_CLOUD_NAME", default="")
if CLOUDINARY_CLOUD_NAME:  # pragma: no cover
    import cloudinary  # type: ignore

    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=config("CLOUDINARY_API_KEY", default=""),
        api_secret=config("CLOUDINARY_API_SECRET", default=""),
        secure=True,
    )

# ---------------------------------------------------------------------------
# Security in production
# ---------------------------------------------------------------------------
if not DEBUG:  # pragma: no cover
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
