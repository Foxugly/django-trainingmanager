#!/usr/bin/env python
"""Django's command-line utility for administrative tasks.

Default settings module: django-trainingmanager.settings.dev

To override (e.g. in production), set the DJANGO_SETTINGS_MODULE
environment variable before invoking the script:

    DJANGO_SETTINGS_MODULE=django-trainingmanager.settings.prod \\
        python manage.py migrate

Or pass the --settings flag explicitly:

    python manage.py shell --settings=django-trainingmanager.settings.prod

In production, this file is typically not invoked: gunicorn / uwsgi
load wsgi.py directly, which uses its own setdefault pattern.
"""

import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django-trainingmanager.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
