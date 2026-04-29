from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone

from member.models import Member
from team.models import TeamInvitation, TeamMembership
from tests.factories import TeamFactory, UserFactory

pytestmark = pytest.mark.django_db


# ----------------------------- POST /invitations/ ----------------------------


def test_POST_create_invitation_as_trainer_returns_201(auth_client_trainer, trainer_user):
    team = trainer_user.owned_teams.first()
    mail.outbox = []
    response = auth_client_trainer.post(
        "/api/v1/invitations/",
        {
            "team": team.pk,
            "email": "newathlete@local.test",
            "firstname": "New",
            "lastname": "Athlete",
        },
        format="json",
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "newathlete@local.test"
    assert "token" not in body
    assert TeamInvitation.objects.filter(
        email="newathlete@local.test", team=team, status="pending"
    ).exists()
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["newathlete@local.test"]
    assert "/invitation/" in mail.outbox[0].body


def test_POST_create_invitation_as_non_trainer_returns_403(auth_client_non_trainer):
    team = TeamFactory()
    response = auth_client_non_trainer.post(
        "/api/v1/invitations/",
        {
            "team": team.pk,
            "email": "someone@local.test",
            "firstname": "A",
            "lastname": "B",
        },
        format="json",
    )
    assert response.status_code == 403


def test_POST_create_invitation_existing_user_links_member(auth_client_trainer, trainer_user):
    existing = UserFactory(email="existing@local.test")
    team = trainer_user.owned_teams.first()
    mail.outbox = []
    response = auth_client_trainer.post(
        "/api/v1/invitations/",
        {
            "team": team.pk,
            "email": "existing@local.test",
            "firstname": "Exi",
            "lastname": "Sting",
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.json().get("member_id") is not None
    member = Member.objects.get(user=existing)
    assert member.memberships.filter(team=team, left_at__isnull=True).exists()
    assert not TeamInvitation.objects.filter(email="existing@local.test").exists()
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["existing@local.test"]
    assert "/invitation/" not in mail.outbox[0].body


def test_POST_create_invitation_duplicate_pending_returns_400(auth_client_trainer, trainer_user):
    team = trainer_user.owned_teams.first()
    payload = {
        "team": team.pk,
        "email": "dup@local.test",
        "firstname": "D",
        "lastname": "P",
    }
    auth_client_trainer.post("/api/v1/invitations/", payload, format="json")
    response = auth_client_trainer.post("/api/v1/invitations/", payload, format="json")
    assert response.status_code == 400


def test_POST_create_invitation_unmanaged_team_returns_400(auth_client_trainer):
    other_team = TeamFactory()
    response = auth_client_trainer.post(
        "/api/v1/invitations/",
        {
            "team": other_team.pk,
            "email": "x@local.test",
            "firstname": "X",
            "lastname": "Y",
        },
        format="json",
    )
    assert response.status_code == 400


# ----------------------------- GET /invitations/ -----------------------------


def test_invitation_token_not_exposed_in_list(auth_client_trainer, trainer_user):
    team = trainer_user.owned_teams.first()
    member = Member.objects.create(firstname="F", lastname="L", email="f@local.test")
    TeamMembership.objects.create(team=team, member=member)
    TeamInvitation.objects.create(team=team, member=member, email="f@local.test")
    response = auth_client_trainer.get("/api/v1/invitations/")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] >= 1
    for r in body["results"]:
        assert "token" not in r


# ----------------------- GET /invitations/lookup/<token>/ --------------------


def test_GET_invitation_lookup_valid_token_returns_200(api_client, trainer_user):
    team = trainer_user.owned_teams.first()
    member = Member.objects.create(firstname="Lu", lastname="Up", email="lu@local.test")
    TeamMembership.objects.create(team=team, member=member)
    inv = TeamInvitation.objects.create(team=team, member=member, email="lu@local.test")
    response = api_client.get(f"/api/v1/invitations/lookup/{inv.token}/")
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "lu@local.test"
    assert body["team_name"] == team.name
    assert body["status"] == "pending"


def test_GET_invitation_lookup_invalid_token_returns_404(api_client):
    response = api_client.get("/api/v1/invitations/lookup/nope-no-such-token/")
    assert response.status_code == 404


def test_GET_invitation_lookup_expired_returns_410(api_client, trainer_user):
    team = trainer_user.owned_teams.first()
    member = Member.objects.create(firstname="Ex", lastname="Pired", email="ex@local.test")
    TeamMembership.objects.create(team=team, member=member)
    inv = TeamInvitation.objects.create(
        team=team,
        member=member,
        email="ex@local.test",
        expires_at=timezone.now() - timedelta(days=1),
    )
    response = api_client.get(f"/api/v1/invitations/lookup/{inv.token}/")
    assert response.status_code == 410
    inv.refresh_from_db()
    assert inv.status == "expired"


# --------------------- POST /invitations/lookup/<token>/ ---------------------


def test_POST_complete_invitation_creates_user_and_jwt(api_client, trainer_user):
    team = trainer_user.owned_teams.first()
    member = Member.objects.create(firstname="Co", lastname="Mplete", email="co@local.test")
    TeamMembership.objects.create(team=team, member=member)
    inv = TeamInvitation.objects.create(team=team, member=member, email="co@local.test")

    response = api_client.post(
        f"/api/v1/invitations/lookup/{inv.token}/",
        {"username": "newathlete", "password": "StrongPass!2026"},
        format="json",
    )
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "newathlete"
    assert "access" in body
    assert "refresh" in body

    inv.refresh_from_db()
    assert inv.status == "completed"
    assert inv.completed_at is not None

    member.refresh_from_db()
    assert member.user is not None
    assert member.user.username == "newathlete"

    from allauth.account.models import EmailAddress

    ea = EmailAddress.objects.get(user=member.user, email="co@local.test")
    assert ea.verified is True
    assert ea.primary is True


def test_POST_complete_invitation_invalid_username_returns_400(api_client, trainer_user):
    UserFactory(username="taken")
    team = trainer_user.owned_teams.first()
    member = Member.objects.create(firstname="F", lastname="L", email="dup@local.test")
    TeamMembership.objects.create(team=team, member=member)
    inv = TeamInvitation.objects.create(team=team, member=member, email="dup@local.test")

    response = api_client.post(
        f"/api/v1/invitations/lookup/{inv.token}/",
        {"username": "taken", "password": "StrongPass!2026"},
        format="json",
    )
    assert response.status_code == 400


def test_POST_complete_invitation_weak_password_returns_400(api_client, trainer_user):
    team = trainer_user.owned_teams.first()
    member = Member.objects.create(firstname="F", lastname="L", email="weak@local.test")
    TeamMembership.objects.create(team=team, member=member)
    inv = TeamInvitation.objects.create(team=team, member=member, email="weak@local.test")

    response = api_client.post(
        f"/api/v1/invitations/lookup/{inv.token}/",
        {"username": "someone", "password": "short"},
        format="json",
    )
    assert response.status_code == 400


def test_POST_complete_invitation_already_used_returns_400(api_client, trainer_user):
    team = trainer_user.owned_teams.first()
    member = Member.objects.create(firstname="F", lastname="L", email="used@local.test")
    TeamMembership.objects.create(team=team, member=member)
    inv = TeamInvitation.objects.create(
        team=team,
        member=member,
        email="used@local.test",
        status="completed",
    )

    response = api_client.post(
        f"/api/v1/invitations/lookup/{inv.token}/",
        {"username": "someone2", "password": "StrongPass!2026"},
        format="json",
    )
    assert response.status_code == 400


# ---------------------- DELETE /invitations/{id}/ ----------------------------


def test_DELETE_invitation_cancels_it(auth_client_trainer, trainer_user):
    team = trainer_user.owned_teams.first()
    member = Member.objects.create(firstname="D", lastname="El", email="del@local.test")
    TeamMembership.objects.create(team=team, member=member)
    inv = TeamInvitation.objects.create(team=team, member=member, email="del@local.test")

    response = auth_client_trainer.delete(f"/api/v1/invitations/{inv.pk}/")
    # ModelViewSet's destroy returns 204
    assert response.status_code == 204
    inv.refresh_from_db()
    assert inv.status == "cancelled"
