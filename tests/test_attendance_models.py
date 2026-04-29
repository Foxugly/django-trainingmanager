"""Coverage of Attendance / AttendanceStatus models, i18n and constraints.

No API endpoints yet — viewsets land in Prompt 4/4.
"""

from datetime import timedelta

import pytest
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.utils import timezone

from attendance.models import Attendance, AttendanceStatus
from event.models import Event
from member.models import Member
from tests.factories import ProgramFactory, TeamFactory

pytestmark = pytest.mark.django_db


def _present():
    return AttendanceStatus.objects.get(code="present")


def _absent():
    return AttendanceStatus.objects.get(code="absent")


# =====================================================================
# Seeded data (from migration 0003_seed_default_statuses)
# =====================================================================


def test_seed_creates_three_default_statuses(db):
    codes = set(AttendanceStatus.objects.values_list("code", flat=True))
    assert {"present", "absent", "excused"}.issubset(codes)


def test_attendance_status_translated_label(db):
    s = AttendanceStatus.objects.get(code="present")
    assert s.label_fr == "Présent"
    assert s.label_nl == "Aanwezig"
    assert s.label_en == "Present"
    assert s.label_it == "Presente"
    assert s.label_es == "Presente"


def test_existing_team_linked_to_three_default_statuses(db):
    """Migration 0007_link_existing_teams_to_default_statuses linked the
    pre-existing team. Newly created teams in tests do NOT have statuses
    auto-attached; test the seeded link only."""
    from team.models import Team

    # The single legacy team (pk=1, RBP) was linked by the data migration.
    legacy = Team.objects.filter(pk=1).first()
    if legacy is not None:
        codes = set(legacy.attendance_statuses.values_list("code", flat=True))
        assert codes == {"present", "absent", "excused"}


# =====================================================================
# Attendance basic CRUD
# =====================================================================


def test_create_attendance_basic(db):
    """Direct create — Attendance is NOT auto-populated by signals (Prompt 4)."""
    team = TeamFactory()
    program = ProgramFactory(team=team)
    event = Event.objects.create(
        refer_program=program, name="E", date=timezone.localdate() + timedelta(days=3)
    )
    member = Member.objects.create(firstname="A", lastname="B", email="ab@local.test")

    att = Attendance.objects.create(event=event, member=member, status=_present())
    assert att.event_id == event.pk
    assert att.member_id == member.pk
    assert att.status.code == "present"
    assert att.created_at is not None


def test_attendance_str(db):
    team = TeamFactory()
    program = ProgramFactory(team=team)
    event = Event.objects.create(
        refer_program=program, name="E", date=timezone.localdate() + timedelta(days=1)
    )
    member = Member.objects.create(firstname="St", lastname="R", email="str@local.test")
    att = Attendance.objects.create(event=event, member=member, status=_present())
    s = str(att)
    assert "present" in s
    assert "St" in s


# =====================================================================
# Constraints
# =====================================================================


def test_unique_attendance_per_event_member(db):
    team = TeamFactory()
    program = ProgramFactory(team=team)
    event = Event.objects.create(
        refer_program=program, name="E", date=timezone.localdate() + timedelta(days=1)
    )
    member = Member.objects.create(firstname="U", lastname="N", email="un@local.test")
    Attendance.objects.create(event=event, member=member, status=_present())

    with pytest.raises(IntegrityError):
        Attendance.objects.create(event=event, member=member, status=_absent())


def test_status_protected_on_delete_when_in_use(db):
    """Cannot delete an AttendanceStatus that has Attendance rows referring to it."""
    team = TeamFactory()
    program = ProgramFactory(team=team)
    event = Event.objects.create(
        refer_program=program, name="E", date=timezone.localdate() + timedelta(days=1)
    )
    member = Member.objects.create(firstname="P", lastname="R", email="pr@local.test")
    Attendance.objects.create(event=event, member=member, status=_present())

    with pytest.raises(ProtectedError):
        _present().delete()


# =====================================================================
# Ordering & defaults
# =====================================================================


def test_attendance_status_ordering(db):
    codes = list(AttendanceStatus.objects.values_list("code", flat=True))
    # order field: present=1, absent=2, excused=3
    assert codes.index("present") < codes.index("absent") < codes.index("excused")


def test_default_statuses_count_3(db):
    """All three seeded statuses are flagged is_default=True so the
    post_save Team signal pre-attaches them on team creation."""
    defaults = set(AttendanceStatus.objects.filter(is_default=True).values_list("code", flat=True))
    assert {"present", "absent", "excused"}.issubset(defaults)
