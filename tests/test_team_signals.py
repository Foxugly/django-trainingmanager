"""Coverage of post_save Team signal: auto-attach default AttendanceStatuses.

Rules:
- On Team creation: attach all AttendanceStatus(is_default=True, is_active=True)
- On Team update: do NOT re-attach (preserves coach customizations)
- Idempotency: skip when team already has statuses (fixture/manual)
- Inactive default statuses are excluded
"""

import pytest

from attendance.models import AttendanceStatus
from tests.factories import TeamFactory

pytestmark = pytest.mark.django_db


def test_creating_team_auto_attaches_default_statuses(db):
    defaults = list(AttendanceStatus.objects.filter(is_default=True, is_active=True))
    assert len(defaults) >= 1, "Seed migration should have produced default statuses"

    team = TeamFactory()

    attached = list(team.attendance_statuses.all())
    for status in defaults:
        assert status in attached
    assert len(attached) == len(defaults)


def test_updating_team_does_not_re_attach_statuses(db):
    team = TeamFactory()
    original = list(team.attendance_statuses.all())
    assert len(original) >= 1

    removed = original[0]
    team.attendance_statuses.remove(removed)
    assert removed not in team.attendance_statuses.all()

    team.name = "Renamed for test"
    team.save()

    refreshed = list(team.attendance_statuses.all())
    assert removed not in refreshed
    assert len(refreshed) == len(original) - 1


def test_creating_team_skips_inactive_default_statuses(db):
    """A status flagged is_default=True but is_active=False must not be attached."""
    absent = AttendanceStatus.objects.get(code="absent")
    absent.is_default = True
    absent.is_active = False
    absent.save(update_fields=["is_default", "is_active"])

    try:
        team = TeamFactory()
        attached_codes = set(team.attendance_statuses.values_list("code", flat=True))
        assert "absent" not in attached_codes
    finally:
        absent.is_default = False
        absent.is_active = True
        absent.save(update_fields=["is_default", "is_active"])
