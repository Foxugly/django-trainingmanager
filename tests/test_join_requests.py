import pytest
from django.core import mail

from member.models import Member
from team.models import TeamJoinRequest
from tests.factories import TeamFactory, UserFactory

pytestmark = pytest.mark.django_db


# ----------------------------- POST ----------------------------------

def test_POST_join_request_returns_201(auth_client, authenticated_user):
    team = TeamFactory(is_active=True, is_public=True)
    response = auth_client.post(
        '/api/v1/join-requests/',
        {'team': team.pk, 'message': 'I want to join'},
        format='json',
    )
    assert response.status_code == 201
    body = response.json()
    assert body['team'] == team.pk
    assert TeamJoinRequest.objects.filter(user=authenticated_user, team=team, status='pending').exists()


def test_POST_join_request_sends_email_to_managers(auth_client):
    owner = UserFactory(email='owner@local.test')
    mgr = UserFactory(email='manager@local.test')
    team = TeamFactory(owner=owner, is_active=True, is_public=True)
    team.managers.add(mgr)

    mail.outbox = []
    response = auth_client.post(
        '/api/v1/join-requests/',
        {'team': team.pk, 'message': 'hi'},
        format='json',
    )
    assert response.status_code == 201
    assert len(mail.outbox) == 1
    assert set(mail.outbox[0].to) == {'owner@local.test', 'manager@local.test'}


def test_POST_join_request_already_member_returns_400(auth_client, authenticated_user):
    team = TeamFactory(is_active=True, is_public=True)
    member = Member.objects.create(
        firstname='Test', lastname='User',
        email='already@local.test', user=authenticated_user,
    )
    member.teams.add(team)
    response = auth_client.post(
        '/api/v1/join-requests/',
        {'team': team.pk},
        format='json',
    )
    assert response.status_code == 400


def test_POST_join_request_duplicate_pending_returns_400(auth_client, authenticated_user):
    team = TeamFactory(is_active=True, is_public=True)
    TeamJoinRequest.objects.create(user=authenticated_user, team=team, status='pending')
    response = auth_client.post(
        '/api/v1/join-requests/',
        {'team': team.pk},
        format='json',
    )
    assert response.status_code == 400


def test_POST_join_request_private_team_returns_400(auth_client):
    team = TeamFactory(is_active=True, is_public=False)
    response = auth_client.post(
        '/api/v1/join-requests/',
        {'team': team.pk},
        format='json',
    )
    assert response.status_code == 400


def test_POST_join_request_inactive_team_returns_400(auth_client):
    team = TeamFactory(is_active=False, is_public=True)
    response = auth_client.post(
        '/api/v1/join-requests/',
        {'team': team.pk},
        format='json',
    )
    assert response.status_code == 400


# ---------------------------- PATCH ----------------------------------

def test_PATCH_accept_join_request_creates_member(auth_client_trainer, trainer_user):
    requester = UserFactory(first_name='Alice', last_name='Wonder')
    team = trainer_user.owned_teams.first()
    jr = TeamJoinRequest.objects.create(user=requester, team=team, status='pending')

    response = auth_client_trainer.patch(
        f'/api/v1/join-requests/{jr.pk}/',
        {'status': 'accepted', 'response_message': 'Welcome'},
        format='json',
    )
    assert response.status_code == 200
    jr.refresh_from_db()
    assert jr.status == 'accepted'
    assert jr.responded_by_id == trainer_user.pk
    assert jr.responded_at is not None
    assert Member.objects.filter(user=requester, teams=team).exists()


def test_PATCH_accept_existing_member_just_adds_team(auth_client_trainer, trainer_user):
    requester = UserFactory()
    other_team = TeamFactory()
    member = Member.objects.create(
        firstname='Bob', lastname='Existing',
        email=requester.email, user=requester,
    )
    member.teams.add(other_team)

    team = trainer_user.owned_teams.first()
    jr = TeamJoinRequest.objects.create(user=requester, team=team, status='pending')
    response = auth_client_trainer.patch(
        f'/api/v1/join-requests/{jr.pk}/',
        {'status': 'accepted'},
        format='json',
    )
    assert response.status_code == 200
    member.refresh_from_db()
    assert team in member.teams.all()
    assert other_team in member.teams.all()
    assert Member.objects.filter(user=requester).count() == 1


def test_PATCH_reject_join_request(auth_client_trainer, trainer_user):
    requester = UserFactory()
    team = trainer_user.owned_teams.first()
    jr = TeamJoinRequest.objects.create(user=requester, team=team, status='pending')

    response = auth_client_trainer.patch(
        f'/api/v1/join-requests/{jr.pk}/',
        {'status': 'rejected', 'response_message': 'Sorry'},
        format='json',
    )
    assert response.status_code == 200
    jr.refresh_from_db()
    assert jr.status == 'rejected'
    assert not Member.objects.filter(user=requester).exists()


def test_PATCH_cancel_own_request(auth_client, authenticated_user):
    team = TeamFactory(is_active=True, is_public=True)
    jr = TeamJoinRequest.objects.create(user=authenticated_user, team=team, status='pending')

    response = auth_client.patch(
        f'/api/v1/join-requests/{jr.pk}/',
        {'status': 'cancelled'},
        format='json',
    )
    assert response.status_code == 200
    jr.refresh_from_db()
    assert jr.status == 'cancelled'
    assert jr.responded_at is not None


def test_PATCH_already_handled_returns_400(auth_client_trainer, trainer_user):
    requester = UserFactory()
    team = trainer_user.owned_teams.first()
    jr = TeamJoinRequest.objects.create(user=requester, team=team, status='accepted')

    response = auth_client_trainer.patch(
        f'/api/v1/join-requests/{jr.pk}/',
        {'status': 'rejected'},
        format='json',
    )
    assert response.status_code == 400


def test_PATCH_other_user_cant_modify(api_client, authenticated_user):
    requester = UserFactory()
    team = TeamFactory(is_active=True, is_public=True)
    jr = TeamJoinRequest.objects.create(user=requester, team=team, status='pending')

    api_client.force_authenticate(user=authenticated_user)
    response = api_client.patch(
        f'/api/v1/join-requests/{jr.pk}/',
        {'status': 'cancelled'},
        format='json',
    )
    assert response.status_code in (403, 404)


def test_PATCH_non_manager_cannot_accept(auth_client, authenticated_user):
    requester = UserFactory()
    team = TeamFactory(is_active=True, is_public=True)
    jr = TeamJoinRequest.objects.create(user=authenticated_user, team=team, status='pending')

    response = auth_client.patch(
        f'/api/v1/join-requests/{jr.pk}/',
        {'status': 'accepted'},
        format='json',
    )
    assert response.status_code == 400
    jr.refresh_from_db()
    assert jr.status == 'pending'


# ----------------------------- GET -----------------------------------

def test_GET_join_requests_user_sees_own_only(auth_client, authenticated_user):
    team_a = TeamFactory(is_active=True, is_public=True)
    team_b = TeamFactory(is_active=True, is_public=True)
    other = UserFactory()
    TeamJoinRequest.objects.create(user=authenticated_user, team=team_a)
    TeamJoinRequest.objects.create(user=other, team=team_b)

    response = auth_client.get('/api/v1/join-requests/')
    assert response.status_code == 200
    body = response.json()
    assert body['count'] == 1
    assert body['results'][0]['user'] == authenticated_user.pk


def test_GET_join_requests_manager_sees_team_requests(auth_client_trainer, trainer_user):
    team = trainer_user.owned_teams.first()
    other = UserFactory()
    TeamJoinRequest.objects.create(user=other, team=team)
    other_team = TeamFactory()
    TeamJoinRequest.objects.create(user=UserFactory(), team=other_team)

    response = auth_client_trainer.get('/api/v1/join-requests/')
    assert response.status_code == 200
    body = response.json()
    assert body['count'] == 1
    assert body['results'][0]['team'] == team.pk
