"""Link every existing Team to the three default AttendanceStatuses.

New teams will have to opt in explicitly (or via a default in code);
this migration only seeds the existing data.
"""

from django.db import migrations


def link_teams_to_default_statuses(apps, schema_editor):
    Team = apps.get_model("team", "Team")
    AttendanceStatus = apps.get_model("attendance", "AttendanceStatus")

    default_statuses = list(
        AttendanceStatus.objects.filter(code__in=["present", "absent", "excused"])
    )
    if not default_statuses:
        print("  WARNING: default statuses not seeded; skipping link")
        return

    linked = 0
    for team in Team.objects.all():
        team.attendance_statuses.set(default_statuses)
        linked += 1
    print(f"  Linked {linked} teams to {len(default_statuses)} default attendance statuses")


def reverse_link(apps, schema_editor):
    Team = apps.get_model("team", "Team")
    for team in Team.objects.all():
        team.attendance_statuses.clear()


class Migration(migrations.Migration):

    dependencies = [
        ("team", "0006_add_attendance_statuses_m2m"),
        ("attendance", "0003_seed_default_statuses"),
    ]

    operations = [
        migrations.RunPython(link_teams_to_default_statuses, reverse_link),
    ]
