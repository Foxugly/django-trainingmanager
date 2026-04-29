"""Coverage of the team chat feature.

URL: /api/v1/teams/{team_id}/messages/

Permissions:
  - Read: any team member (owner / manager / athlete via Member.user)
  - Write create: respects team.chat_mode
      'all'           -> any team member
      'coaches_only'  -> only owner/managers
  - Update / delete: author OR team owner/manager
"""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from chat.models import Message
from member.models import Member
from tests.factories import TeamFactory

pytestmark = pytest.mark.django_db


User = get_user_model()


# ----------------------------- fixtures ----------------------------


@pytest.fixture
def coach_user(db):
    return User.objects.create_user(
        username="chat_coach", email="chat_coach@local.test", password="pass"
    )


@pytest.fixture
def manager_user(db):
    return User.objects.create_user(
        username="chat_manager", email="chat_manager@local.test", password="pass"
    )


@pytest.fixture
def athlete_user(db):
    return User.objects.create_user(
        username="chat_athlete", email="chat_athlete@local.test", password="pass"
    )


@pytest.fixture
def random_user(db):
    return User.objects.create_user(
        username="chat_random", email="chat_random@local.test", password="pass"
    )


@pytest.fixture
def chat_team(coach_user, manager_user, athlete_user):
    """Team where coach is owner, manager_user is manager, athlete_user is a Member."""
    team = TeamFactory(owner=coach_user, is_active=True)
    team.managers.add(manager_user)
    member = Member.objects.create(
        firstname="A",
        lastname="Thlete",
        email=athlete_user.email,
        user=athlete_user,
    )
    member.teams.add(team)
    return team


@pytest.fixture
def coach_client(api_client, coach_user):
    api_client.force_authenticate(user=coach_user)
    return api_client


@pytest.fixture
def manager_client(api_client, manager_user):
    api_client.force_authenticate(user=manager_user)
    return api_client


@pytest.fixture
def athlete_client(api_client, athlete_user):
    api_client.force_authenticate(user=athlete_user)
    return api_client


@pytest.fixture
def random_client(api_client, random_user):
    api_client.force_authenticate(user=random_user)
    return api_client


def _url(team_id, msg_id=None):
    base = f"/api/v1/teams/{team_id}/messages/"
    return base if msg_id is None else f"{base}{msg_id}/"


# ============================ MODEL =================================


def test_create_message_basic(chat_team, coach_user):
    msg = Message.objects.create(team=chat_team, author=coach_user, content="<p>hi</p>")
    assert msg.is_deleted is False
    assert msg.edited_at is None


def test_str_representation(chat_team, coach_user):
    msg = Message.objects.create(team=chat_team, author=coach_user, content="x")
    assert "chat_coach" in str(msg)


def test_str_indicates_edited(chat_team, coach_user):
    msg = Message.objects.create(team=chat_team, author=coach_user, content="x")
    msg.edited_at = timezone.now()
    msg.save()
    assert "[edited]" in str(msg)


def test_str_indicates_deleted(chat_team, coach_user):
    msg = Message.objects.create(team=chat_team, author=coach_user, content="x")
    msg.deleted_at = timezone.now()
    msg.save()
    assert "[deleted]" in str(msg)


def test_is_deleted_property(chat_team, coach_user):
    msg = Message.objects.create(team=chat_team, author=coach_user, content="x")
    assert msg.is_deleted is False
    msg.deleted_at = timezone.now()
    msg.save()
    assert msg.is_deleted is True


# ===================== PERMISSIONS LECTURE ==========================


def test_owner_can_list_messages(coach_client, chat_team):
    response = coach_client.get(_url(chat_team.pk))
    assert response.status_code == 200


def test_manager_can_list_messages(manager_client, chat_team):
    response = manager_client.get(_url(chat_team.pk))
    assert response.status_code == 200


def test_athlete_member_can_list_messages(athlete_client, chat_team):
    response = athlete_client.get(_url(chat_team.pk))
    assert response.status_code == 200


def test_random_user_cannot_access_messages(random_client, chat_team):
    response = random_client.get(_url(chat_team.pk))
    assert response.status_code == 403


def test_anonymous_cannot_access_messages(api_client, chat_team):
    response = api_client.get(_url(chat_team.pk))
    assert response.status_code == 401


# =================== PERMISSIONS WRITE — chat_mode 'all' ============


def test_owner_can_post_when_mode_all(coach_client, chat_team):
    response = coach_client.post(_url(chat_team.pk), {"content": "<p>hi</p>"}, format="json")
    assert response.status_code == 201


def test_manager_can_post_when_mode_all(manager_client, chat_team):
    response = manager_client.post(_url(chat_team.pk), {"content": "<p>hi</p>"}, format="json")
    assert response.status_code == 201


def test_athlete_can_post_when_mode_all(athlete_client, chat_team):
    response = athlete_client.post(_url(chat_team.pk), {"content": "<p>hi</p>"}, format="json")
    assert response.status_code == 201


# ============== PERMISSIONS WRITE — chat_mode 'coaches_only' ========


def test_owner_can_post_when_mode_coaches_only(coach_client, chat_team):
    chat_team.chat_mode = "coaches_only"
    chat_team.save(update_fields=["chat_mode"])
    response = coach_client.post(_url(chat_team.pk), {"content": "<p>hi</p>"}, format="json")
    assert response.status_code == 201


def test_manager_can_post_when_mode_coaches_only(manager_client, chat_team):
    chat_team.chat_mode = "coaches_only"
    chat_team.save(update_fields=["chat_mode"])
    response = manager_client.post(_url(chat_team.pk), {"content": "<p>hi</p>"}, format="json")
    assert response.status_code == 201


def test_athlete_cannot_post_when_mode_coaches_only(athlete_client, chat_team):
    chat_team.chat_mode = "coaches_only"
    chat_team.save(update_fields=["chat_mode"])
    response = athlete_client.post(_url(chat_team.pk), {"content": "<p>hi</p>"}, format="json")
    assert response.status_code == 403


# ========================= EDIT ====================================


def test_author_can_edit_own_message(athlete_client, chat_team, athlete_user):
    msg = Message.objects.create(team=chat_team, author=athlete_user, content="<p>old</p>")
    response = athlete_client.patch(
        _url(chat_team.pk, msg.pk), {"content": "<p>new</p>"}, format="json"
    )
    assert response.status_code == 200
    msg.refresh_from_db()
    assert msg.content == "<p>new</p>"


def test_owner_can_edit_anyone_message(coach_client, chat_team, athlete_user):
    msg = Message.objects.create(team=chat_team, author=athlete_user, content="<p>x</p>")
    response = coach_client.patch(
        _url(chat_team.pk, msg.pk), {"content": "<p>edited by coach</p>"}, format="json"
    )
    assert response.status_code == 200


def test_manager_can_edit_anyone_message(manager_client, chat_team, athlete_user):
    msg = Message.objects.create(team=chat_team, author=athlete_user, content="<p>x</p>")
    response = manager_client.patch(
        _url(chat_team.pk, msg.pk), {"content": "<p>edited by manager</p>"}, format="json"
    )
    assert response.status_code == 200


def test_other_member_cannot_edit_someone_else_message(
    api_client, chat_team, athlete_user, coach_user
):
    msg = Message.objects.create(team=chat_team, author=coach_user, content="<p>boss</p>")
    api_client.force_authenticate(user=athlete_user)
    response = api_client.patch(
        _url(chat_team.pk, msg.pk), {"content": "<p>tampered</p>"}, format="json"
    )
    assert response.status_code == 403


def test_edit_sets_edited_at_timestamp(athlete_client, chat_team, athlete_user):
    msg = Message.objects.create(team=chat_team, author=athlete_user, content="<p>x</p>")
    assert msg.edited_at is None
    response = athlete_client.patch(
        _url(chat_team.pk, msg.pk), {"content": "<p>y</p>"}, format="json"
    )
    assert response.status_code == 200
    msg.refresh_from_db()
    assert msg.edited_at is not None


# ========================= DELETE (soft) ===========================


def test_author_can_delete_own_message(athlete_client, chat_team, athlete_user):
    msg = Message.objects.create(team=chat_team, author=athlete_user, content="x")
    response = athlete_client.delete(_url(chat_team.pk, msg.pk))
    assert response.status_code == 204
    msg.refresh_from_db()
    assert msg.deleted_at is not None


def test_owner_can_delete_anyone_message(coach_client, chat_team, athlete_user):
    msg = Message.objects.create(team=chat_team, author=athlete_user, content="x")
    response = coach_client.delete(_url(chat_team.pk, msg.pk))
    assert response.status_code == 204


def test_other_member_cannot_delete_someone_else_message(
    api_client, chat_team, athlete_user, coach_user
):
    msg = Message.objects.create(team=chat_team, author=coach_user, content="x")
    api_client.force_authenticate(user=athlete_user)
    response = api_client.delete(_url(chat_team.pk, msg.pk))
    assert response.status_code == 403


def test_delete_sets_deleted_at_not_hard_delete(coach_client, chat_team, coach_user):
    msg = Message.objects.create(team=chat_team, author=coach_user, content="x")
    response = coach_client.delete(_url(chat_team.pk, msg.pk))
    assert response.status_code == 204
    assert Message.objects.filter(pk=msg.pk).exists()
    msg.refresh_from_db()
    assert msg.deleted_at is not None


def test_deleted_message_still_visible_in_list_with_deleted_at(coach_client, chat_team, coach_user):
    msg = Message.objects.create(
        team=chat_team, author=coach_user, content="x", deleted_at=timezone.now()
    )
    response = coach_client.get(_url(chat_team.pk))
    ids = [r["id"] for r in response.json()]
    assert msg.pk in ids


# ========================= PAGINATION ==============================


def test_initial_load_returns_default_50_most_recent(coach_client, chat_team, coach_user):
    for i in range(60):
        Message.objects.create(team=chat_team, author=coach_user, content=f"msg{i}")
    response = coach_client.get(_url(chat_team.pk))
    assert response.status_code == 200
    assert len(response.json()) == 50


def test_initial_load_with_limit_param(coach_client, chat_team, coach_user):
    for i in range(20):
        Message.objects.create(team=chat_team, author=coach_user, content=f"msg{i}")
    response = coach_client.get(_url(chat_team.pk) + "?limit=5")
    assert response.status_code == 200
    assert len(response.json()) == 5


def test_limit_capped_at_max_200(coach_client, chat_team, coach_user):
    for i in range(250):
        Message.objects.create(team=chat_team, author=coach_user, content=f"msg{i}")
    response = coach_client.get(_url(chat_team.pk) + "?limit=999")
    assert response.status_code == 200
    assert len(response.json()) == 200


def test_polling_with_since_returns_only_newer(coach_client, chat_team, coach_user):
    base = timezone.now() - timedelta(hours=1)
    old = Message.objects.create(team=chat_team, author=coach_user, content="old")
    Message.objects.filter(pk=old.pk).update(created_at=base)
    new = Message.objects.create(team=chat_team, author=coach_user, content="new")
    Message.objects.filter(pk=new.pk).update(created_at=timezone.now() + timedelta(seconds=1))

    cutoff = base + timedelta(minutes=30)
    response = coach_client.get(_url(chat_team.pk), {"since": cutoff.isoformat()})
    ids = [r["id"] for r in response.json()]
    assert new.pk in ids
    assert old.pk not in ids


def test_scroll_back_with_before_returns_only_older(coach_client, chat_team, coach_user):
    old = Message.objects.create(team=chat_team, author=coach_user, content="old")
    Message.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(hours=2))
    new = Message.objects.create(team=chat_team, author=coach_user, content="new")
    Message.objects.filter(pk=new.pk).update(created_at=timezone.now())

    cutoff = timezone.now() - timedelta(hours=1)
    response = coach_client.get(_url(chat_team.pk), {"before": cutoff.isoformat()})
    ids = [r["id"] for r in response.json()]
    assert old.pk in ids
    assert new.pk not in ids


# ======================= SANITIZATION ==============================


def test_content_is_sanitized_on_create(coach_client, chat_team):
    response = coach_client.post(
        _url(chat_team.pk),
        {"content": '<p>Hello</p><script>alert("xss")</script>'},
        format="json",
    )
    assert response.status_code == 201
    body = response.json()
    assert "<script>" not in body["content"]
    assert "<p>Hello</p>" in body["content"]


def test_empty_content_returns_400(coach_client, chat_team):
    response = coach_client.post(_url(chat_team.pk), {"content": ""}, format="json")
    assert response.status_code == 400


# ======================= AUTHOR TRACKING ===========================


def test_create_sets_author_to_current_user(coach_client, chat_team, coach_user):
    response = coach_client.post(_url(chat_team.pk), {"content": "<p>hi</p>"}, format="json")
    assert response.status_code == 201
    msg = Message.objects.get(pk=response.json()["id"])
    assert msg.author_id == coach_user.pk


def test_author_is_serialized_with_username(coach_client, chat_team, coach_user):
    response = coach_client.post(_url(chat_team.pk), {"content": "<p>hi</p>"}, format="json")
    assert response.json()["author_username"] == coach_user.username
