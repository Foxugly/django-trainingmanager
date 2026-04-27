import logging

import httpx
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from msal import ConfidentialClientApplication

logger = logging.getLogger(__name__)


class GraphEmailBackend(BaseEmailBackend):
    """Backend Django utilisant Microsoft Graph API /sendMail."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = None
        self._token = None

    def _get_token(self):
        if self._token:
            return self._token
        if not self._app:
            self._app = ConfidentialClientApplication(
                client_id=settings.GRAPH_CLIENT_ID,
                client_credential=settings.GRAPH_CLIENT_SECRET,
                authority=f"https://login.microsoftonline.com/{settings.GRAPH_TENANT_ID}",
            )
        result = self._app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        if "access_token" not in result:
            raise RuntimeError(f"Graph auth failed: {result.get('error_description')}")
        self._token = result["access_token"]
        return self._token

    def send_messages(self, email_messages):
        sent = 0
        for msg in email_messages:
            try:
                self._send_one(msg)
                sent += 1
            except Exception as e:
                logger.exception("Failed to send email via Graph: %s", e)
                if not self.fail_silently:
                    raise
        return sent

    def _send_one(self, msg):
        token = self._get_token()
        sender = settings.GRAPH_SENDER
        url = f"https://graph.microsoft.com/v1.0/users/{sender}/sendMail"

        is_html = msg.content_subtype == "html"
        graph_msg = {
            "message": {
                "subject": msg.subject,
                "body": {
                    "contentType": "HTML" if is_html else "Text",
                    "content": msg.body,
                },
                "toRecipients": [{"emailAddress": {"address": addr}} for addr in msg.to],
            },
            "saveToSentItems": False,
        }
        if msg.cc:
            graph_msg["message"]["ccRecipients"] = [
                {"emailAddress": {"address": a}} for a in msg.cc
            ]
        if msg.bcc:
            graph_msg["message"]["bccRecipients"] = [
                {"emailAddress": {"address": a}} for a in msg.bcc
            ]

        response = httpx.post(
            url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=graph_msg,
            timeout=30,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Graph sendMail failed: {response.status_code} {response.text}")
