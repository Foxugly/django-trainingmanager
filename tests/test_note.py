"""Coverage of the Note feature.

URL pattern: /api/v1/teams/{team_id}/members/{member_id}/notes/

Permissions:
  - Coach (team owner / managers): full CRUD
  - Athlete (member.user == request.user): read own notes only when
    team.athlete_can_read_notes is True
  - Soft-deleted notes never visible to athletes
"""

import pytest
from django.contrib.auth import get_user_model

from member.models import Member
from note.models import Note
from tests.factories import TeamFactory

pytestmark = pytest.mark.django_db


User = get_user_model()


@pytest.fixture
def coach_user(db):
    return User.objects.create_user(
        username="coach1", email="coach1@local.test", password="passcoach"
    )


@pytest.fixture
def coach_team(coach_user):
    return TeamFactory(owner=coach_user, is_active=True)


@pytest.fixture
def athlete_user(db):
    return User.objects.create_user(
        username="athlete1", email="athlete1@local.test", password="passathlete"
    )


@pytest.fixture
def member_in_team(athlete_user, coach_team):
    member = Member.objects.create(
        firstname="Alex",
        lastname="Athlete",
        email="alex@local.test",
        user=athlete_user,
    )
    member.teams.add(coach_team)
    return member


@pytest.fixture
def coach_client(api_client, coach_user):
    api_client.force_authenticate(user=coach_user)
    return api_client


@pytest.fixture
def athlete_client(api_client, athlete_user):
    api_client.force_authenticate(user=athlete_user)
    return api_client


@pytest.fixture
def random_user(db):
    return User.objects.create_user(
        username="rando", email="rando@local.test", password="passrando"
    )


@pytest.fixture
def random_client(api_client, random_user):
    api_client.force_authenticate(user=random_user)
    return api_client


def _url(team_id, member_id, note_id=None):
    base = f"/api/v1/teams/{team_id}/members/{member_id}/notes/"
    return base if note_id is None else f"{base}{note_id}/"


# =====================================================================
# MODEL
# =====================================================================


def test_create_note_basic(coach_team, member_in_team, coach_user):
    note = Note.objects.create(
        team=coach_team,
        member=member_in_team,
        author=coach_user,
        content="<p>Test</p>",
    )
    assert note.is_active is True
    assert note.team_id == coach_team.pk
    assert note.member_id == member_in_team.pk
    assert note.author_id == coach_user.pk


def test_str_representation(coach_team, member_in_team, coach_user):
    note = Note.objects.create(
        team=coach_team, member=member_in_team, author=coach_user, content="x"
    )
    s = str(note)
    assert "coach1" in s
    assert "Alex" in s or "Athlete" in s


def test_str_handles_deleted_author(coach_team, member_in_team):
    note = Note.objects.create(team=coach_team, member=member_in_team, author=None, content="x")
    assert "(deleted)" in str(note)


# =====================================================================
# CRUD COACH
# =====================================================================


def test_owner_can_create_note(coach_client, coach_team, member_in_team):
    response = coach_client.post(
        _url(coach_team.pk, member_in_team.pk),
        {"content": "<p>Bonne séance aujourd'hui</p>"},
        format="json",
    )
    assert response.status_code == 201, response.json()
    body = response.json()
    assert body["content"] == "<p>Bonne séance aujourd'hui</p>"
    assert body["author_username"] == "coach1"


def test_manager_can_create_note(api_client, coach_team, member_in_team, athlete_user):
    """Add athlete_user as a manager and verify they can create notes."""
    coach_team.managers.add(athlete_user)
    api_client.force_authenticate(user=athlete_user)
    response = api_client.post(
        _url(coach_team.pk, member_in_team.pk),
        {"content": "<p>Manager note</p>"},
        format="json",
    )
    assert response.status_code == 201


def test_random_user_cannot_create_note(random_client, coach_team, member_in_team):
    response = random_client.post(
        _url(coach_team.pk, member_in_team.pk),
        {"content": "<p>x</p>"},
        format="json",
    )
    assert response.status_code == 403


def test_owner_can_list_notes(coach_client, coach_team, member_in_team, coach_user):
    Note.objects.create(team=coach_team, member=member_in_team, author=coach_user, content="A")
    Note.objects.create(team=coach_team, member=member_in_team, author=coach_user, content="B")
    response = coach_client.get(_url(coach_team.pk, member_in_team.pk))
    assert response.status_code == 200
    assert response.json()["count"] == 2


def test_owner_can_patch_note(coach_client, coach_team, member_in_team, coach_user):
    note = Note.objects.create(
        team=coach_team, member=member_in_team, author=coach_user, content="<p>old</p>"
    )
    response = coach_client.patch(
        _url(coach_team.pk, member_in_team.pk, note.pk),
        {"content": "<p>new</p>"},
        format="json",
    )
    assert response.status_code == 200
    note.refresh_from_db()
    assert note.content == "<p>new</p>"


def test_owner_can_soft_delete_note(coach_client, coach_team, member_in_team, coach_user):
    note = Note.objects.create(
        team=coach_team, member=member_in_team, author=coach_user, content="x"
    )
    response = coach_client.delete(_url(coach_team.pk, member_in_team.pk, note.pk))
    assert response.status_code == 204
    note.refresh_from_db()
    assert note.is_active is False


def test_soft_deleted_notes_excluded_by_default(
    coach_client, coach_team, member_in_team, coach_user
):
    Note.objects.create(team=coach_team, member=member_in_team, author=coach_user, content="active")
    Note.objects.create(
        team=coach_team, member=member_in_team, author=coach_user, content="dead", is_active=False
    )
    response = coach_client.get(_url(coach_team.pk, member_in_team.pk))
    assert response.json()["count"] == 1


def test_owner_can_see_inactive_with_include_inactive(
    coach_client, coach_team, member_in_team, coach_user
):
    Note.objects.create(team=coach_team, member=member_in_team, author=coach_user, content="active")
    Note.objects.create(
        team=coach_team, member=member_in_team, author=coach_user, content="dead", is_active=False
    )
    response = coach_client.get(_url(coach_team.pk, member_in_team.pk) + "?include_inactive=true")
    assert response.json()["count"] == 2


# =====================================================================
# ATHLETE
# =====================================================================


def test_athlete_cannot_read_when_flag_false(
    athlete_client, coach_team, member_in_team, coach_user
):
    """Default: team.athlete_can_read_notes=False -> athlete gets 403."""
    Note.objects.create(team=coach_team, member=member_in_team, author=coach_user, content="x")
    response = athlete_client.get(_url(coach_team.pk, member_in_team.pk))
    assert response.status_code == 403


def test_athlete_can_read_own_notes_when_flag_true(
    athlete_client, coach_team, member_in_team, coach_user
):
    coach_team.athlete_can_read_notes = True
    coach_team.save(update_fields=["athlete_can_read_notes"])
    Note.objects.create(team=coach_team, member=member_in_team, author=coach_user, content="hello")
    response = athlete_client.get(_url(coach_team.pk, member_in_team.pk))
    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_athlete_cannot_read_other_member_notes_even_when_flag_true(
    athlete_client, coach_team, member_in_team, coach_user
):
    """Another Member, same team, with the flag on -> still 403 for our athlete."""
    coach_team.athlete_can_read_notes = True
    coach_team.save(update_fields=["athlete_can_read_notes"])
    other = Member.objects.create(firstname="Other", lastname="Person", email="other@local.test")
    other.teams.add(coach_team)
    Note.objects.create(team=coach_team, member=other, author=coach_user, content="secret")
    response = athlete_client.get(_url(coach_team.pk, other.pk))
    assert response.status_code == 403


def test_athlete_cannot_see_soft_deleted_even_with_include_inactive(
    athlete_client, coach_team, member_in_team, coach_user
):
    coach_team.athlete_can_read_notes = True
    coach_team.save(update_fields=["athlete_can_read_notes"])
    Note.objects.create(team=coach_team, member=member_in_team, author=coach_user, content="alive")
    Note.objects.create(
        team=coach_team,
        member=member_in_team,
        author=coach_user,
        content="dead",
        is_active=False,
    )
    response = athlete_client.get(_url(coach_team.pk, member_in_team.pk) + "?include_inactive=true")
    assert response.status_code == 200
    assert response.json()["count"] == 1


def test_athlete_cannot_create_note(athlete_client, coach_team, member_in_team):
    coach_team.athlete_can_read_notes = True
    coach_team.save(update_fields=["athlete_can_read_notes"])
    response = athlete_client.post(
        _url(coach_team.pk, member_in_team.pk),
        {"content": "<p>I'm just an athlete</p>"},
        format="json",
    )
    assert response.status_code == 403


# =====================================================================
# VALIDATION
# =====================================================================


def test_create_note_for_member_not_in_team_returns_403(coach_client, coach_team, athlete_user):
    """Member exists but not attached to coach_team."""
    other = Member.objects.create(firstname="Out", lastname="Sider", email="out@local.test")
    response = coach_client.post(
        _url(coach_team.pk, other.pk),
        {"content": "<p>x</p>"},
        format="json",
    )
    assert response.status_code == 403


def test_content_is_sanitized_on_create(coach_client, coach_team, member_in_team):
    payload = '<p>Hello</p><script>alert("xss")</script>'
    response = coach_client.post(
        _url(coach_team.pk, member_in_team.pk),
        {"content": payload},
        format="json",
    )
    assert response.status_code == 201
    body = response.json()
    assert "<script>" not in body["content"]
    assert "<p>Hello</p>" in body["content"]


def test_content_is_sanitized_on_patch(coach_client, coach_team, member_in_team, coach_user):
    note = Note.objects.create(
        team=coach_team, member=member_in_team, author=coach_user, content="<p>ok</p>"
    )
    response = coach_client.patch(
        _url(coach_team.pk, member_in_team.pk, note.pk),
        {"content": '<p>ok</p><iframe src="evil"></iframe>'},
        format="json",
    )
    assert response.status_code == 200
    note.refresh_from_db()
    assert "<iframe" not in note.content


# =====================================================================
# AUTHOR TRACKING
# =====================================================================


def test_create_note_sets_author_to_current_user(
    coach_client, coach_team, member_in_team, coach_user
):
    response = coach_client.post(
        _url(coach_team.pk, member_in_team.pk),
        {"content": "<p>x</p>"},
        format="json",
    )
    assert response.status_code == 201
    note = Note.objects.get(pk=response.json()["id"])
    assert note.author_id == coach_user.pk


def test_author_set_null_if_user_deleted(coach_team, member_in_team):
    """Use a second coach (manager, not the team owner) as author so
    we can delete them without tripping the Team.owner PROTECT FK."""
    second_coach = User.objects.create_user(
        username="coach2_for_authornull",
        email="coach2_an@local.test",
        password="passcoach",
    )
    coach_team.managers.add(second_coach)
    note = Note.objects.create(
        team=coach_team, member=member_in_team, author=second_coach, content="x"
    )
    second_coach.delete()
    note.refresh_from_db()
    assert note.author is None
