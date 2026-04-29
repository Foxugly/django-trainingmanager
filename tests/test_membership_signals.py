"""Coverage of the auto-sync signals between TeamMembership and Event.members.

Rules under test:
  - Creating an active TeamMembership attaches the member to all FUTURE
    events of the team (date >= today).
  - Setting left_at on a TeamMembership detaches the member from all
    FUTURE events (past events are preserved for historical integrity).
  - Creating a new Event attaches all currently active members of the
    team (resolved via refer_program.team).
  - Members who left the team are NOT attached to newly created events.
  - PATCH /api/v1/events/{id}/ with `members` is silently ignored
    (Event.members is read-only in the API).
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from event.models import Event
from member.models import Member
from team.models import TeamMembership
from tests.factories import ProgramFactory, TeamFactory

pytestmark = pytest.mark.django_db


def _future_date():
    return timezone.localdate() + timedelta(days=7)


def _past_date():
    return timezone.localdate() - timedelta(days=7)


# =====================================================================
# TeamMembership creation -> attach to future events
# =====================================================================


def test_creating_membership_auto_attaches_to_future_events(db):
    team = TeamFactory()
    program = ProgramFactory(team=team)
    future_event = Event.objects.create(refer_program=program, name="F", date=_future_date())
    assert future_event.members.count() == 0

    member = Member.objects.create(firstname="N", lastname="M", email="nm@local.test")
    TeamMembership.objects.create(team=team, member=member)

    future_event.refresh_from_db()
    assert member in future_event.members.all()


def test_creating_membership_does_not_attach_to_past_events(db):
    team = TeamFactory()
    program = ProgramFactory(team=team)
    past_event = Event.objects.create(refer_program=program, name="P", date=_past_date())
    future_event = Event.objects.create(refer_program=program, name="F", date=_future_date())

    member = Member.objects.create(firstname="N", lastname="M", email="nm2@local.test")
    TeamMembership.objects.create(team=team, member=member)

    assert member not in past_event.members.all()
    assert member in future_event.members.all()


def test_creating_membership_other_team_does_not_leak(db):
    team_a = TeamFactory()
    team_b = TeamFactory()
    program_b = ProgramFactory(team=team_b)
    event_b = Event.objects.create(refer_program=program_b, name="B", date=_future_date())

    member = Member.objects.create(firstname="N", lastname="M", email="nm3@local.test")
    TeamMembership.objects.create(team=team_a, member=member)

    assert member not in event_b.members.all()


# =====================================================================
# TeamMembership end (left_at set) -> detach from future events
# =====================================================================


def test_ending_membership_detaches_from_future_events(db):
    team = TeamFactory()
    program = ProgramFactory(team=team)
    future_event = Event.objects.create(refer_program=program, name="F", date=_future_date())

    member = Member.objects.create(firstname="N", lastname="M", email="nm4@local.test")
    ms = TeamMembership.objects.create(team=team, member=member)
    assert member in future_event.members.all()

    ms.left_at = timezone.now()
    ms.save(update_fields=["left_at"])

    future_event.refresh_from_db()
    assert member not in future_event.members.all()


def test_ending_membership_keeps_member_in_past_events(db):
    team = TeamFactory()
    program = ProgramFactory(team=team)
    past_event = Event.objects.create(refer_program=program, name="P", date=_past_date())

    member = Member.objects.create(firstname="N", lastname="M", email="nm5@local.test")
    ms = TeamMembership.objects.create(team=team, member=member)
    # Past events are not auto-attached on creation; we manually attach to
    # mimic legacy data, then verify cleanup leaves them intact.
    past_event.members.add(member)

    ms.left_at = timezone.now()
    ms.save(update_fields=["left_at"])

    assert member in past_event.members.all()


# =====================================================================
# Event creation -> attach active members of team
# =====================================================================


def test_creating_event_attaches_all_active_members(db):
    team = TeamFactory()
    program = ProgramFactory(team=team)
    members = [
        Member.objects.create(firstname=f"A{i}", lastname="X", email=f"a{i}@local.test")
        for i in range(3)
    ]
    for m in members:
        TeamMembership.objects.create(team=team, member=m)

    event = Event.objects.create(refer_program=program, name="New", date=_future_date())

    attached_ids = set(event.members.values_list("pk", flat=True))
    assert attached_ids == {m.pk for m in members}


def test_creating_event_excludes_left_members(db):
    team = TeamFactory()
    program = ProgramFactory(team=team)
    active = Member.objects.create(firstname="Act", lastname="Ive", email="ai@local.test")
    left = Member.objects.create(firstname="Le", lastname="Ft", email="lft@local.test")
    TeamMembership.objects.create(team=team, member=active)
    ms_left = TeamMembership.objects.create(team=team, member=left)
    ms_left.left_at = timezone.now()
    ms_left.save(update_fields=["left_at"])

    event = Event.objects.create(refer_program=program, name="New", date=_future_date())
    assert active in event.members.all()
    assert left not in event.members.all()


def test_creating_event_without_program_does_not_crash(db):
    """Orphan event (no refer_program) -> signal is a no-op, no error."""
    event = Event.objects.create(name="Orphan", date=_future_date())
    assert event.members.count() == 0


# =====================================================================
# API: Event.members read-only
# =====================================================================


def test_PATCH_event_members_is_ignored(auth_client_trainer, trainer_user):
    program = ProgramFactory(team=trainer_user.owned_teams.first())
    event = Event.objects.create(refer_program=program, name="API", date=_future_date())

    extra = Member.objects.create(firstname="Ex", lastname="Tra", email="ex@local.test")
    before = list(event.members.values_list("pk", flat=True))

    response = auth_client_trainer.patch(
        f"/api/v1/events/{event.pk}/",
        {"members": [extra.pk]},
        format="json",
    )
    assert response.status_code == 200
    event.refresh_from_db()
    after = list(event.members.values_list("pk", flat=True))
    assert after == before
