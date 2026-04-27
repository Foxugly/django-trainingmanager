import pytest
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model

from tests.factories import TeamFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_user(db):
    User = get_user_model()
    user = User.objects.create_user(
        username='testuser',
        email='testuser@local.test',
        password='Str0ngP@ssTest!',
    )
    return user


@pytest.fixture
def auth_client(api_client, authenticated_user):
    api_client.force_authenticate(user=authenticated_user)
    return api_client


@pytest.fixture
def user_team(authenticated_user):
    return TeamFactory(owner=authenticated_user)
