#!/usr/bin/env python
"""manage.py — local development entry point.

This script ALWAYS forces DJANGO_SETTINGS_MODULE to
'django-trainingmanager.settings.dev', overriding any value injected by
the host environment (IDE Run Configuration, shell exports, etc.).
That keeps `python manage.py runserver` reliable: no more cryptic
"ALLOWED_HOSTS must be set if DEBUG is False" when an IDE silently
points it at .prod.

Production never invokes manage.py — it goes through wsgi.py /
asgi.py with DJANGO_SETTINGS_MODULE explicitly set in the deploy
environment.

Escape hatch: if you ever need to run a management command against
prod settings locally, pass the flag explicitly:
    python manage.py <cmd> --settings=django-trainingmanager.settings.prod
"""

import os
import sys

if __name__ == "__main__":
    if not any(arg.startswith("--settings=") for arg in sys.argv):
        os.environ["DJANGO_SETTINGS_MODULE"] = "django-trainingmanager.settings.dev"
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
