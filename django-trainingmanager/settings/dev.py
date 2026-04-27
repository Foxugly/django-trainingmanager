from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

INTERNAL_IPS = ['127.0.0.1']
if 'debug_toolbar.middleware.DebugToolbarMiddleware' not in MIDDLEWARE:
    MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + list(MIDDLEWARE)
