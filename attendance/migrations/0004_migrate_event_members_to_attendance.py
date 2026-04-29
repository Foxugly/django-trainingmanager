"""Backfill Attendance rows from legacy event.members M2M.

For every (event, member) pair in the legacy `event.members` M2M, create
an Attendance row with status='present'. Members not listed in
event.members are *not* given an Attendance row — there is no honest
default for "unknown".

Idempotent via get_or_create on (event, member).
"""

from django.db import migrations


def migrate_event_members(apps, schema_editor):
    Event = apps.get_model("event", "Event")
    Attendance = apps.get_model("attendance", "Attendance")
    AttendanceStatus = apps.get_model("attendance", "AttendanceStatus")

    try:
        present_status = AttendanceStatus.objects.get(code="present")
    except AttendanceStatus.DoesNotExist:
        print("  WARNING: 'present' status not found, skipping legacy migration")
        return

    created = 0
    skipped = 0
    for event in Event.objects.all():
        for member in event.members.all():
            _, was_created = Attendance.objects.get_or_create(
                event=event,
                member=member,
                defaults={"status": present_status},
            )
            if was_created:
                created += 1
            else:
                skipped += 1
    print(
        f"  Created {created} Attendance rows (status='present'), "
        f"skipped {skipped} (already existed)"
    )


def reverse_migration(apps, schema_editor):
    """Heuristic reverse: drop all Attendance rows whose status='present'.

    Imperfect — if the user already added non-legacy 'present' rows
    via the API, those will also be dropped. Acceptable for dev rollback;
    in production this migration is one-way in spirit.
    """
    Attendance = apps.get_model("attendance", "Attendance")
    AttendanceStatus = apps.get_model("attendance", "AttendanceStatus")
    try:
        present_status = AttendanceStatus.objects.get(code="present")
        count, _ = Attendance.objects.filter(status=present_status).delete()
        print(f"  Removed {count} Attendance rows on reverse migration")
    except AttendanceStatus.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ("attendance", "0003_seed_default_statuses"),
        ("team", "0007_link_existing_teams_to_default_statuses"),
        ("event", "0004_event_created_at_event_updated_at"),
    ]

    operations = [
        migrations.RunPython(migrate_event_members, reverse_migration),
    ]
