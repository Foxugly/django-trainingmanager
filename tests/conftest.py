import pytest
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model

from tests.factories import TeamFactory


@pytest.fixture(autouse=True)
def use_locmem_email_backend(settings):
    """Block real Graph email sends across the test suite."""
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'


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


@pytest.fixture
def trainer_user(db):
    User = get_user_model()
    user = User.objects.create_user(
        username='trainer',
        email='trainer@local.test',
        password='Str0ngP@ssTrainer!',
    )
    TeamFactory(owner=user, is_active=True)
    return user


@pytest.fixture
def auth_client_trainer(api_client, trainer_user):
    api_client.force_authenticate(user=trainer_user)
    return api_client


@pytest.fixture
def non_trainer_user(db):
    User = get_user_model()
    return User.objects.create_user(
        username='spectator',
        email='spectator@local.test',
        password='Str0ngP@ssSpec!',
    )


@pytest.fixture
def auth_client_non_trainer(api_client, non_trainer_user):
    api_client.force_authenticate(user=non_trainer_user)
    return api_client
