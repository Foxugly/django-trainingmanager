"""Coverage of POST /api/v1/members/ — clean 400 instead of 500.

Reproduces and verifies the fix for the IntegrityError-on-O2O-conflict
bug reported by the frontend during Prompt #8.
"""

import pytest
from django.contrib.auth import get_user_model

from member.models import Member
from tests.factories import TeamFactory

pytestmark = pytest.mark.django_db


User = get_user_model()


@pytest.fixture
def manager_user(db):
    user = User.objects.create_user(
        username="mc_manager", email="mc_manager@local.test", password="pass"
    )
    TeamFactory(owner=user, is_active=True)
    return user


@pytest.fixture
def manager_client(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)
    return api_client


@pytest.fixture
def free_user(db):
    return User.objects.create_user(username="mc_free", email="mc_free@local.test", password="pass")


@pytest.fixture
def busy_user(db):
    """User who already has a Member profile."""
    user = User.objects.create_user(username="mc_busy", email="mc_busy@local.test", password="pass")
    Member.objects.create(firstname="Busy", lastname="User", email=user.email, user=user)
    return user


URL = "/api/v1/members/"


def test_POST_member_minimal_payload_returns_201(manager_client):
    """firstname + lastname is enough — email is nullable, user optional."""
    response = manager_client.post(
        URL,
        {"firstname": "Mike", "lastname": "Doe"},
        format="json",
    )
    assert response.status_code == 201, response.json()


def test_POST_member_missing_required_returns_400_unified(manager_client):
    """firstname missing -> 400 with unified error format."""
    response = manager_client.post(
        URL,
        {"lastname": "Doe"},
        format="json",
    )
    assert response.status_code == 400
    body = response.json()
    assert body.get("code") == "validation_error"
    assert "fields" in body
    assert "firstname" in body["fields"]


def test_POST_member_with_user_already_in_use_returns_400(manager_client, busy_user):
    """O2O conflict is caught upfront, not at DB level."""
    response = manager_client.post(
        URL,
        {
            "firstname": "Renaud",
            "lastname": "Test",
            "email": "renaud_test@example.com",
            "user_id": busy_user.pk,
        },
        format="json",
    )
    assert response.status_code == 400, response.json()
    body = response.json()
    assert body.get("code") == "validation_error"
    assert "user_id" in body.get("fields", {})


def test_POST_member_with_unused_user_returns_201(manager_client, free_user):
    """Free user (no existing Member) -> 201."""
    response = manager_client.post(
        URL,
        {
            "firstname": "Renaud",
            "lastname": "Test",
            "email": "renaud_free@example.com",
            "user_id": free_user.pk,
        },
        format="json",
    )
    assert response.status_code == 201, response.json()
    assert Member.objects.filter(user=free_user).exists()
