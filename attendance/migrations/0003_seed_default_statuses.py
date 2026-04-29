"""Seed the three default attendance statuses (present / absent / excused).

Labels are populated for the 5 supported languages directly into the
modeltranslation columns (label_fr, label_nl, label_en, label_it, label_es)
and the canonical `label` (defaults to French, the project default).
"""

from django.db import migrations

DEFAULT_STATUSES = [
    {
        "code": "present",
        "label": "Présent",
        "label_fr": "Présent",
        "label_nl": "Aanwezig",
        "label_en": "Present",
        "label_it": "Presente",
        "label_es": "Presente",
        "is_default": True,
        "order": 1,
        "color": "#10b981",
    },
    {
        "code": "absent",
        "label": "Absent",
        "label_fr": "Absent",
        "label_nl": "Afwezig",
        "label_en": "Absent",
        "label_it": "Assente",
        "label_es": "Ausente",
        "is_default": False,
        "order": 2,
        "color": "#ef4444",
    },
    {
        "code": "excused",
        "label": "Excusé",
        "label_fr": "Excusé",
        "label_nl": "Gerechtvaardigd",
        "label_en": "Excused",
        "label_it": "Giustificato",
        "label_es": "Justificado",
        "is_default": False,
        "order": 3,
        "color": "#f59e0b",
    },
]


def seed_statuses(apps, schema_editor):
    AttendanceStatus = apps.get_model("attendance", "AttendanceStatus")
    for data in DEFAULT_STATUSES:
        AttendanceStatus.objects.update_or_create(
            code=data["code"],
            defaults=data,
        )
    print(f"  Seeded {len(DEFAULT_STATUSES)} default AttendanceStatus")


def reverse_seed(apps, schema_editor):
    AttendanceStatus = apps.get_model("attendance", "AttendanceStatus")
    AttendanceStatus.objects.filter(code__in=["present", "absent", "excused"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("attendance", "0002_add_label_translations"),
    ]

    operations = [
        migrations.RunPython(seed_statuses, reverse_seed),
    ]
