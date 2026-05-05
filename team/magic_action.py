"""HMAC-signed magic links for one-click accept/reject of TeamJoinRequest.

Format: TimestampSigner.sign(f"{join_request_id}:{action}") with a 7-day
max-age. No DB row — the signature is the entire credential. A token
is replayable until it expires; the actual transition is idempotent
(see views.TeamJoinRequestMagicActionView).

Two-step interaction so Outlook safe-links / Gmail link previewers
can't accidentally trigger the action:
  - GET ?token=...  -> view returns the proposed action + current state
  - POST {token, confirm: true} -> view executes the action
"""

from django.conf import settings
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner

ALLOWED_ACTIONS = ("accept", "reject")
TOKEN_MAX_AGE_SECONDS = 7 * 24 * 3600  # 7 days
SIGNER_SALT = "team.join_request.magic_action"


def _signer() -> TimestampSigner:
    return TimestampSigner(salt=SIGNER_SALT)


def make_token(join_request_id: int, action: str) -> str:
    """Return an HMAC-signed token encoding (join_request_id, action).

    `action` must be in ALLOWED_ACTIONS. Tokens expire 7 days after issue."""
    if action not in ALLOWED_ACTIONS:
        raise ValueError(f"action must be one of {ALLOWED_ACTIONS}, got {action!r}")
    return _signer().sign(f"{join_request_id}:{action}")


def parse_token(token: str) -> tuple[int, str] | None:
    """Reverse of make_token. Returns (join_request_id, action) or None on
    any failure (bad signature, expired, malformed payload)."""
    try:
        raw = _signer().unsign(token, max_age=TOKEN_MAX_AGE_SECONDS)
    except (SignatureExpired, BadSignature):
        return None
    try:
        jr_id_str, action = raw.split(":", 1)
        jr_id = int(jr_id_str)
    except (ValueError, AttributeError):
        return None
    if action not in ALLOWED_ACTIONS:
        return None
    return jr_id, action


def magic_link(join_request_id: int, action: str) -> str:
    """Build the absolute URL the manager will receive in the email."""
    base = settings.FRONTEND_URL.rstrip("/")
    token = make_token(join_request_id, action)
    return f"{base}/team-join-requests/magic-action/{token}/"
