from .base import *  # noqa: F401, F403

DEBUG = False

# ---------------------- SSL / TLS ------------------------------------
# Redirect every HTTP hit to HTTPS at the Django layer; the reverse proxy
# in front (nginx / Caddy / a load balancer) is expected to terminate TLS
# and forward the original scheme via the X-Forwarded-Proto header so
# Django can detect the secure origin.
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ---------------------- HSTS -----------------------------------------
# 1 year, includeSubDomains, preload-eligible. Once a browser has seen
# this header on the apex domain it will refuse plain HTTP for the whole
# subdomain tree until the TTL expires — which is why this is gated on
# DEBUG=False (i.e. prod settings only): activating it locally would make
# any HTTP localhost preview break.
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ---------------------- Cookies / CSRF -------------------------------
# Cookies are only sent over HTTPS, never readable from JS, with a
# Lax SameSite (the standard balance — protects against CSRF while
# keeping top-level navigation flows working). HttpOnly on the CSRF
# cookie too: Django reads it server-side, not from JS — DRF's
# JWT-authenticated endpoints don't need a CSRF token at all, and the
# admin reads the value from the request, not from JS.
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

X_FRAME_OPTIONS = "DENY"

# CORS_ALLOWED_ORIGINS is now read from the environment in base.py — no
# code change needed at deploy time, set CORS_ALLOWED_ORIGINS in the
# prod .env (comma-separated, e.g.
#   CORS_ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com
# ).
