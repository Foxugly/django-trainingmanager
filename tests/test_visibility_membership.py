"""Regression tests for the team visibility fix.

Background: a user who is an active TeamMembership of a private team
was previously NOT included in /teams/, /programs/, /events/ or /members/
queryset filters. The helper team.queries.user_visible_teams now
includes the membership branch.

Coverage matrix:
  - active member of private team -> sees team / programs / events / members
  - ex-member (left_at set) -> does NOT see the team anymore
  - random user -> does NOT see private team, sees public team
  - owner / manager -> still see their team (regression)
"""

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from event.models import Event
from member.models import Member
from program.models import Program
from team.models import TeamMembership
from tests.factories import TeamFactory

pytestmark = pytest.mark.django_db


User = get_user_model()


@pytest.fixture
def coach_user(db):
    return User.objects.create_user(
        username="vis_coach", email="vis_coach@local.test", password="pass"
    )


@pytest.fixture
def private_team(coach_user):
    return TeamFactory(owner=coach_user, is_active=True, is_public=False)


@pytest.fixture
def athlete_user(db):
    return User.objects.create_user(
        username="vis_athlete", email="vis_athlete@local.test", password="pass"
    )


@pytest.fixture
def athlete_member_of_private(athlete_user, private_team):
    member = Member.objects.create(
        firstname="V", lastname="A", email=athlete_user.email, user=athlete_user
    )
    TeamMembership.objects.create(team=private_team, member=member)
    return member


@pytest.fixture
def athlete_client(api_client, athlete_user):
    api_client.force_authenticate(user=athlete_user)
    return api_client


@pytest.fixture
def random_client(api_client, db):
    user = User.objects.create_user(
        username="vis_rando", email="vis_rando@local.test", password="pass"
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def coach_client(api_client, coach_user):
    api_client.force_authenticate(user=coach_user)
    return api_client


def _ids(payload, key):
    """Extract IDs from a paginated or flat list payload."""
    items = payload.get("results", payload) if isinstance(payload, dict) else payload
    return [row[key] for row in items]


# =====================================================================
# /teams/  visibility
# =====================================================================


def test_active_member_sees_private_team_in_list(
    athlete_client, private_team, athlete_member_of_private
):
    response = athlete_client.get("/api/v1/teams/")
    assert response.status_code == 200
    assert private_team.pk in _ids(response.json(), "id")


def test_active_member_can_retrieve_private_team(
    athlete_client, private_team, athlete_member_of_private
):
    response = athlete_client.get(f"/api/v1/teams/{private_team.pk}/")
    assert response.status_code == 200


def test_ex_member_does_not_see_private_team(
    athlete_client, private_team, athlete_member_of_private
):
    ms = TeamMembership.objects.get(
        team=private_team, member=athlete_member_of_private, left_at__isnull=True
    )
    ms.left_at = timezone.now()
    ms.save(update_fields=["left_at"])

    response = athlete_client.get("/api/v1/teams/")
    assert response.status_code == 200
    assert private_team.pk not in _ids(response.json(), "id")


def test_random_user_does_not_see_private_team(random_client, private_team):
    response = random_client.get(f"/api/v1/teams/{private_team.pk}/")
    assert response.status_code == 404


def test_random_user_sees_public_active_team(random_client):
    public_team = TeamFactory(is_active=True, is_public=True)
    response = random_client.get(f"/api/v1/teams/{public_team.pk}/")
    assert response.status_code == 200


def test_owner_still_sees_team(coach_client, private_team):
    response = coach_client.get(f"/api/v1/teams/{private_team.pk}/")
    assert response.status_code == 200


def test_manager_still_sees_team(api_client, private_team):
    manager = User.objects.create_user(
        username="vis_mgr", email="vis_mgr@local.test", password="pass"
    )
    private_team.managers.add(manager)
    api_client.force_authenticate(user=manager)
    response = api_client.get(f"/api/v1/teams/{private_team.pk}/")
    assert response.status_code == 200


# =====================================================================
# /programs/, /events/, /members/  cascade
# =====================================================================


def test_active_member_sees_programs_of_private_team(
    athlete_client, private_team, athlete_member_of_private
):
    program = Program.objects.create(name="Prog priv", team=private_team)
    response = athlete_client.get("/api/v1/programs/")
    assert response.status_code == 200
    assert program.pk in _ids(response.json(), "id")


def test_active_member_sees_events_of_private_team(
    athlete_client, private_team, athlete_member_of_private
):
    program = Program.objects.create(name="Prog priv 2", team=private_team)
    event = Event.objects.create(refer_program=program, name="E", date=None)
    response = athlete_client.get("/api/v1/events/")
    assert response.status_code == 200
    assert event.pk in _ids(response.json(), "id")


def test_active_member_sees_self_in_members(
    athlete_client, private_team, athlete_member_of_private
):
    response = athlete_client.get("/api/v1/members/")
    assert response.status_code == 200
    assert athlete_member_of_private.pk in _ids(response.json(), "id")
