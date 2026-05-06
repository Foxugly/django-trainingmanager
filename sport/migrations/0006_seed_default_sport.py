"""Seed the default Sport (Natation) for fresh-clone bootstrap.

Replaces the historical workflow where a dev would `loaddata db.json`
to populate referentials. Idempotent via slug-based update_or_create.
Only the canonical Natation row is seeded; additional sports are added
by staff via the admin.
"""

from django.db import migrations

DEFAULT_SPORTS = [
    {
        "slug": "natation",
        "name": "Natation",
        "name_fr": "Natation",
        "name_nl": "Zwemmen",
        "name_en": "Swimming",
        "name_it": "Nuoto",
        "name_es": "Natación",
        "is_active": True,
    },
]


def seed_sports(apps, schema_editor):
    Sport = apps.get_model("sport", "Sport")
    for data in DEFAULT_SPORTS:
        Sport.objects.update_or_create(slug=data["slug"], defaults=data)


def reverse_noop(apps, schema_editor):
    # Don't auto-delete — referentials may be linked to user-created teams.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("sport", "0005_backfill_name_fr"),
    ]
    operations = [
        migrations.RunPython(seed_sports, reverse_noop),
    ]
