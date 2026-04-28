from datetime import timedelta
from pathlib import Path

import environ
from django.conf import settings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")

DEBUG = env.bool("DEBUG", default=True)
STATE = env("STATE", default="INT")
WEBSITE = env("WEBSITE", default="www.example.com")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "debug_toolbar",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "drf_spectacular",
    "django_filters",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.headless",
    "sport",
    "ai",
    "program",
    "event",
    "round",
    "exercise",
    "member",
    "customuser",
    "team",
]

SITE_ID = 1

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "tools.middleware.UserLanguageMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "django-trainingmanager.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "django-trainingmanager.wsgi.application"

DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3"),
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("fr", "Français"),
    ("nl", "Nederlands"),
    ("en", "English"),
    ("it", "Italiano"),
    ("es", "Español"),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

AUTH_USER_MODEL = "customuser.CustomUser"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: settings.DEBUG,
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_THROTTLE_CLASSES": [],
    "DEFAULT_THROTTLE_RATES": {
        "ai_ping": "30/hour",
        "ai_plan_generation": "10/hour",
        "ai_training_generation": "10/hour",
    },
    "EXCEPTION_HANDLER": "tools.exceptions.custom_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Training Manager API",
    "DESCRIPTION": "API pour la gestion d entrainements",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "ENUM_NAME_OVERRIDES": {
        "JoinRequestStatusEnum": "team.models.TeamJoinRequest.STATUS_CHOICES",
        "InvitationStatusEnum": "team.models.TeamInvitation.STATUS_CHOICES",
        "OverlapStrategyEnum": "program.choices.OVERLAP_STRATEGY_CHOICES",
    },
}

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_SIGNUP_FIELDS = ["username*", "email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USER_MODEL_USERNAME_FIELD = "username"
ACCOUNT_USER_MODEL_EMAIL_FIELD = "email"

HEADLESS_ONLY = True
FRONTEND_URL = env("FRONTEND_URL")
HEADLESS_FRONTEND_URLS = {
    "account_confirm_email": FRONTEND_URL + "/auth/confirm-email/{key}",
    "account_reset_password_from_key": FRONTEND_URL + "/auth/reset-password/{key}",
}

GRAPH_TENANT_ID = env("GRAPH_TENANT_ID")
GRAPH_CLIENT_ID = env("GRAPH_CLIENT_ID")
GRAPH_CLIENT_SECRET = env("GRAPH_CLIENT_SECRET")
GRAPH_SENDER = env("GRAPH_SENDER")

EMAIL_BACKEND = "tools.email.GraphEmailBackend"
DEFAULT_FROM_EMAIL = env("GRAPH_SENDER")

ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", default="")
ANTHROPIC_MODEL_DEFAULT = env("ANTHROPIC_MODEL_DEFAULT", default="claude-haiku-4-5-20251001")
ANTHROPIC_MAX_TOKENS_DEFAULT = env.int("ANTHROPIC_MAX_TOKENS_DEFAULT", default=2048)
ANTHROPIC_TIMEOUT_SECONDS = env.int("ANTHROPIC_TIMEOUT_SECONDS", default=60)
