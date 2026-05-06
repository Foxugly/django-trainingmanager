"""Seed the 'unknown' AttendanceStatus and align the canonical color palette.

`unknown` (gray, order=0, default) was added in dev for the case "haven't
recorded attendance yet". The default colors for present/absent/excused
were also adjusted: `excused` moved from amber to sky-blue to match the
agreed palette (gray / green / red / blue).
"""

from django.db import migrations

UNKNOWN_STATUS = {
    "code": "unknown",
    "label": "Inconnu",
    "label_fr": "Inconnu",
    "label_nl": "Onbekend",
    "label_en": "Unknown",
    "label_it": "Sconosciuto",
    "label_es": "Desconocido",
    "is_default": True,
    "order": 0,
    "color": "#9ca3af",
    "is_active": True,
}

COLOR_ALIGNMENT = {
    "present": "#10b981",
    "absent": "#ef4444",
    "excused": "#38bdf8",
}


def seed_and_align(apps, schema_editor):
    AttendanceStatus = apps.get_model("attendance", "AttendanceStatus")
    AttendanceStatus.objects.update_or_create(
        code=UNKNOWN_STATUS["code"],
        defaults=UNKNOWN_STATUS,
    )
    for code, color in COLOR_ALIGNMENT.items():
        AttendanceStatus.objects.filter(code=code).update(color=color)


def reverse_noop(apps, schema_editor):
    # Don't auto-delete the unknown status — Attendance rows may already
    # reference it. Manual cleanup if ever rolled back.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("attendance", "0005_flip_default_for_absent_excused"),
    ]
    operations = [
        migrations.RunPython(seed_and_align, reverse_noop),
    ]
