"""Lightweight health endpoint for external monitoring (UptimeRobot).

Returns 200 + {"status": "ok", "db": "ok"} when the DB is reachable, else 503.
Proxied by nginx to gunicorn so it exercises the whole chain. See OPERATIONS.md §3.9.
"""
from django.db import connections
from django.db.utils import Error as DBError
from django.http import JsonResponse


def health(request):
    db_ok = True
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DBError:
        db_ok = False
    return JsonResponse(
        {"status": "ok" if db_ok else "error", "db": "ok" if db_ok else "error"},
        status=200 if db_ok else 503,
    )
