"""Copy Member.teams M2M rows into TeamMembership.

joined_at = team.created_at (semantically honest: members were part of
the team at least since team creation; we have no better signal in
historical data).
left_at  = NULL (all current members are considered active).
"""

from django.db import migrations


def migrate_to_membership(apps, schema_editor):
    Member = apps.get_model("member", "Member")
    TeamMembership = apps.get_model("team", "TeamMembership")

    created = 0
    for member in Member.objects.all():
        for team in member.teams.all():
            TeamMembership.objects.create(
                team=team,
                member=member,
                joined_at=team.created_at,
                left_at=None,
            )
            created += 1
    print(f"  Created {created} TeamMembership rows from Member.teams M2M")


def reverse_migration(apps, schema_editor):
    TeamMembership = apps.get_model("team", "TeamMembership")
    Member = apps.get_model("member", "Member")  # noqa: F841 (kept for symmetry)

    for ms in TeamMembership.objects.filter(left_at__isnull=True):
        ms.member.teams.add(ms.team)
    TeamMembership.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("team", "0004_add_team_membership"),
        ("member", "0003_member_created_at_member_updated_at"),
    ]

    operations = [
        migrations.RunPython(migrate_to_membership, reverse_migration),
    ]
