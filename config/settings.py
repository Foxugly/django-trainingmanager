import os
import sys

import environ
from django.utils.translation import gettext_lazy as _

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Config is environment-driven (bare names) so prod secrets come from SSM →
# /run/trainingmanager/.env (systemd EnvironmentFile); dev reads a local .env.
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# No real default for SECRET_KEY in prod: the old hard-coded key was leaked in
# git history and MUST be rotated — a fresh value lives only in SSM.
SECRET_KEY = env("SECRET_KEY", default="dev-insecure-change-me-in-production")

DEBUG = env.bool("DEBUG", default=False)
STATE = env("STATE", default="INT")  # INT / ACC / PROD — also the Sentry env
WEBSITE = env("WEBSITE", default="www.example.com")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',
    'qr_code',
    'hijack',
    'hijack.contrib.admin',
    'wkhtmltopdf',
    'agenda',
    'event',
    'round',
    'exercise',
    'member',
    'customuser',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# django-debug-toolbar: only wired in when DEBUG (never in prod). It refuses to
# run with DEBUG=False anyway, but keeping it out of INSTALLED_APPS/MIDDLEWARE/urls
# avoids the always-True SHOW_TOOLBAR_CALLBACK that shipped on the box.
if DEBUG and "test" not in sys.argv:
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.insert(1, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    DEBUG_TOOLBAR_CONFIG = {'SHOW_TOOLBAR_CALLBACK': lambda request: True}

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'), ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'libraries': {
                'common_tags': 'common_tags',
                'admin.urls': 'django.contrib.admin.templatetags.admin_urls',
            },
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database — env-driven on the fleet DB_* 6-var convention (OPERATIONS.md §3.5).
# Unset DB_* (dev / pre-migration) → sqlite at BASE_DIR/db.sqlite3; prod uses the
# local PostgreSQL (DB_ENGINE=postgresql, DB_HOST=127.0.0.1, ...) via SSM.
_DB_ENGINE_ALIASES = {
    "sqlite3": "django.db.backends.sqlite3",
    "postgresql": "django.db.backends.postgresql",
    "postgres": "django.db.backends.postgresql",
}
_db_engine = env("DB_ENGINE", default="sqlite3")
DATABASES = {
    "default": {
        "ENGINE": _DB_ENGINE_ALIASES.get(_db_engine, _db_engine),
        "NAME": env("DB_NAME", default=os.path.join(BASE_DIR, "db.sqlite3")),
        "USER": env("DB_USER", default=""),
        "PASSWORD": env("DB_PASSWORD", default=""),
        "HOST": env("DB_HOST", default=""),
        "PORT": env("DB_PORT", default=""),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

LANGUAGES = (
    ('en', _('English')),
    ('fr', _('Français')),
    ('nl', _('Nederlands')),
)

STATICFILES_FINDERS = [
    # searches in STATICFILES_DIRS
    'django.contrib.staticfiles.finders.FileSystemFinder',
    # searches in STATIC subfolder of each app
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

WKHTMLTOPDF_CMD = '/usr/bin/wkhtmltopdf'
WKHTMLTOPDF_CMD_OPTIONS = {
    'enable-local-file-access': True,
    'load-error-handling': 'ignore',
    'load-media-error-handling': 'ignore',
}

HIJACK_LOGIN_REDIRECT_URL = '/'
HIJACK_LOGOUT_REDIRECT_URL = '/'
HIJACK_DISPLAY_WARNINGS = True
HIJACK_USE_BOOTSTRAP = True
# HIJACK_ALLOW_GET_REQUESTS left at the secure default (False): account switching
# is POST-only (CSRF-protected). The admin hijack button uses POST; no template
# uses a GET hijack link.

# if AUTH_USER_MODEL then HIJACK_REGISTER_ADMIN = False
HIJACK_REGISTER_ADMIN = False
AUTH_USER_MODEL = "customuser.CustomUser"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Security headers (enforced only outside DEBUG; nginx terminates TLS) ------
# Behind nginx, requests already arrive over TLS with X-Forwarded-Proto=https, so
# Django sees them as secure. SECURE_SSL_REDIRECT is a harmless extra guard
# (nginx also redirects); set it False via env if you prefer nginx-only.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
if not DEBUG:
    SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = env.int("HSTS_SECONDS", default=0)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("HSTS_INCLUDE_SUBDOMAINS", default=False)
    SECURE_HSTS_PRELOAD = env.bool("HSTS_PRELOAD", default=False)

# --- Sentry — optional. Set SENTRY_DSN to enable. ----------------------------
SENTRY_DSN = env("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from django.core.exceptions import DisallowedHost

    def _drop_benign_noise(event, hint):
        # Drop DisallowedHost (raw-IP scanners hitting the box) — the rejection
        # is correct behaviour, not an error worth paging on. Do NOT add the IP
        # to ALLOWED_HOSTS.
        exc = hint.get("exc_info")
        if exc and isinstance(exc[1], DisallowedHost):
            return None
        return event

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        environment=STATE,
        traces_sample_rate=0.1,
        send_default_pii=False,
        before_send=_drop_benign_noise,
    )
