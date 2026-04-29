"""Align AttendanceStatus.is_default semantics with auto-attach behavior.

Decision (post Prompt 4/4): is_default means "pre-attached to every new
team via the post_save Team signal". The earlier seed flagged only
'present' as is_default=True, leaving 'absent' and 'excused' off — but
the desired UX is for all 3 default statuses to be attached on team
creation. We flip both flags now.

Note: the UI "pre-selected" semantics (which row is checked by default
in the attendance form) is conveyed by `order` instead — smallest
order wins.
"""

from django.db import migrations


def flip_defaults(apps, schema_editor):
    AttendanceStatus = apps.get_model("attendance", "AttendanceStatus")
    updated = AttendanceStatus.objects.filter(code__in=["absent", "excused"]).update(
        is_default=True
    )
    print(f"  Flipped is_default=True for {updated} AttendanceStatus rows")


def revert_defaults(apps, schema_editor):
    AttendanceStatus = apps.get_model("attendance", "AttendanceStatus")
    AttendanceStatus.objects.filter(code__in=["absent", "excused"]).update(is_default=False)


class Migration(migrations.Migration):

    dependencies = [
        ("attendance", "0004_migrate_event_members_to_attendance"),
    ]

    operations = [
        migrations.RunPython(flip_defaults, revert_defaults),
    ]
