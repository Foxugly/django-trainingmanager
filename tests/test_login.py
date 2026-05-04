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
