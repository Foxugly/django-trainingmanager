"""Custom allauth adapter that points the email confirmation URL at the
frontend route.

We disabled allauth.headless (its API surface was dormant, replaced by
our own /auth/register/ + /auth/email/confirm/ endpoints). Without
HEADLESS_FRONTEND_URLS, allauth would default to its own template view
for `account_confirm_email` — but we don't have templates. Override
the URL builder so confirmation mails carry the frontend route the
SPA already handles.
"""

from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings


class FrontendAccountAdapter(DefaultAccountAdapter):
    def get_email_confirmation_url(self, request, emailconfirmation):
        base = settings.FRONTEND_URL.rstrip("/")
        return f"{base}/auth/confirm-email/{emailconfirmation.key}"
