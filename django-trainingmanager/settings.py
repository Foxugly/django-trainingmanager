import os
from django.utils.translation import ugettext_lazy as _

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = 'ke2rim3a=ukld9cjh6$d$fb%ztgobvrs807i^d!_whg%@n^%v#'

DEBUG = True
STATE = 'INT' # or ACC or PROD
WEBSITE = "www.example.com"

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'bootstrap_modal_forms',
    'widget_tweaks',
    'qr_code',
    #'debug_toolbar',
    #'hijack',
    #'compat',
    #'hijack_admin',
    #'bootstrap4',
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
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'django-trainingmanager.urls'

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

WSGI_APPLICATION = 'django-trainingmanager.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
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

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
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
#ACTIVE TO PROD / COMMENT TO TEST
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
# COMMENT TO PROD / ACTIVE TO TEST
#STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static'), ]
WKHTMLTOPDF_CMD = '/usr/bin/wkhtmltopdf'

HIJACK_LOGIN_REDIRECT_URL = '/'
HIJACK_LOGOUT_REDIRECT_URL = '/'
HIJACK_DISPLAY_WARNINGS = True
HIJACK_USE_BOOTSTRAP = True
HIJACK_ALLOW_GET_REQUESTS = True

# if AUTH_USER_MODEL then HIJACK_REGISTER_ADMIN = False
HIJACK_REGISTER_ADMIN = False
AUTH_USER_MODEL = "customuser.CustomUser"

if DEBUG:
    def show_toolbar(request):
        return True

    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': 'sportplan.settings.show_toolbar',
    }

