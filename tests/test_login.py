"""Coverage of POST /api/v1/auth/token/ — JWT login with email-verification gate.

VerifiedTokenObtainPairSerializer refuses login for users whose primary
EmailAddress is not yet verified. Legacy users (no EmailAddress at all)
are allowed through for backwards compatibility — there's no data
migration; the verification gate engages once allauth has registered
the user.
"""

import pytest
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db


User = get_user_model()
TOKEN_URL = "/api/v1/auth/token/"


def _make_user(username="login_user", password="Sup3rS@fePass!", verified=None):
    """Create a user. `verified` controls whether an EmailAddress row is
    attached: True = verified, False = unverified, None = no EmailAddress
    at all (legacy)."""
    user = User.objects.create_user(
        username=username,
        email=f"{username}@local.test",
        password=password,
    )
    if verified is True:
        EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
    elif verified is False:
        EmailAddress.objects.create(user=user, email=user.email, verified=False, primary=True)
    return user


def test_login_with_verified_user_returns_tokens(api_client):
    _make_user(username="verified_login", verified=True)
    response = api_client.post(
        TOKEN_URL,
        {"username": "verified_login", "password": "Sup3rS@fePass!"},
        format="json",
    )
    assert response.status_code == 200, response.json()
    body = response.json()
    assert "access" in body and "refresh" in body


def test_login_with_unverified_user_returns_400_email_not_verified(api_client):
    _make_user(username="unverified_login", verified=False)
    response = api_client.post(
        TOKEN_URL,
        {"username": "unverified_login", "password": "Sup3rS@fePass!"},
        format="json",
    )
    assert response.status_code == 400, response.json()
    assert response.json()["code"] == "email_not_verified"


def test_login_with_legacy_user_no_emailaddress_is_allowed(api_client):
    """Backwards compat: users that predate the allauth integration have
    no EmailAddress row. They keep being able to log in until an
    EmailAddress lands on their account."""
    _make_user(username="legacy_login", verified=None)
    response = api_client.post(
        TOKEN_URL,
        {"username": "legacy_login", "password": "Sup3rS@fePass!"},
        format="json",
    )
    assert response.status_code == 200, response.json()
    assert "access" in response.json()


# =====================================================================
# remember=true extends the refresh token TTL (access TTL untouched)
# =====================================================================


def _decode_token_exp(token_str):
    """Decode the JWT payload (without signature verification — we trust
    our own minted tokens) and return the `exp` epoch."""
    import base64
    import json

    payload_b64 = token_str.split(".")[1]
    payload_b64 += "=" * (-len(payload_b64) % 4)  # pad
    return json.loads(base64.urlsafe_b64decode(payload_b64))["exp"]


def test_login_without_remember_short_refresh_ttl(api_client):
    _make_user(username="rem_short", verified=True)
    response = api_client.post(
        TOKEN_URL,
        {"username": "rem_short", "password": "Sup3rS@fePass!"},
        format="json",
    )
    assert response.status_code == 200
    body = response.json()
    refresh_exp = _decode_token_exp(body["refresh"])
    access_exp = _decode_token_exp(body["access"])
    # Default REFRESH_TOKEN_LIFETIME = 7 days; difference between exp and
    # now should be in [6.5d, 7.5d]. Loose bounds to dodge timing flakiness.
    import time

    delta_days = (refresh_exp - time.time()) / 86400
    assert 6.5 < delta_days < 7.5, f"refresh delta {delta_days} not ~7 days"
    # Access TTL is 60 minutes — make sure remember does NOT touch it.
    delta_access_min = (access_exp - time.time()) / 60
    assert 50 < delta_access_min < 70


def test_login_with_remember_extends_refresh_to_30_days(api_client):
    _make_user(username="rem_long", verified=True)
    response = api_client.post(
        TOKEN_URL,
        {"username": "rem_long", "password": "Sup3rS@fePass!", "remember": True},
        format="json",
    )
    assert response.status_code == 200, response.json()
    body = response.json()
    refresh_exp = _decode_token_exp(body["refresh"])
    access_exp = _decode_token_exp(body["access"])
    # REFRESH_TOKEN_LIFETIME_REMEMBER = 30 days; expect [29d, 31d].
    import time

    delta_days = (refresh_exp - time.time()) / 86400
    assert 29 < delta_days < 31, f"refresh delta {delta_days} not ~30 days"
    # Access still on standard 60 minutes
    delta_access_min = (access_exp - time.time()) / 60
    assert 50 < delta_access_min < 70
