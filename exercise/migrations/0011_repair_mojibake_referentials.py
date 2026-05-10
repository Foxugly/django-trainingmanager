"""Defensive cleanup of mojibake (double-encoded UTF-8) in referential rows.

Some early dev databases (pre-i18n era) contain rows where accented
characters were double-encoded — e.g. "Apnée" stored as "Apnée" (the
UTF-8 bytes C3 A9 of "é" re-encoded a second time as C3 83 C2 A9).

This migration detects mojibake by signature (a string that, re-encoded
as latin-1 and decoded as UTF-8, yields a strictly shorter valid string)
and repairs in place. It is a no-op on clean databases.

Caveat: if mojibake is already present when 0009_seed_referentials runs,
0009 will fail with `UNIQUE constraint failed: exercise_modality.name_nl,
exercise_modality.sport_id` (the canonical French name lookup misses the
corrupted row, then INSERT collides on a non-corrupted unique field). In
that case, repair the rows manually first via:

    UPDATE exercise_modality SET name=?, name_fr=? WHERE id=...

then `manage.py migrate` will resume past 0009 and this migration will
sweep up any remaining stragglers.
"""

from django.db import migrations

TARGETS = [
    ("Modality", ("name", "name_fr", "name_nl", "name_en", "name_it", "name_es")),
    ("EnergySystem", ("name", "name_fr", "name_nl", "name_en", "name_it", "name_es")),
    (
        "EnergySegment",
        (
            "description",
            "description_fr",
            "description_nl",
            "description_en",
            "description_it",
            "description_es",
        ),
    ),
]


def _is_mojibake(value):
    if not value:
        return False
    try:
        repaired = value.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return False
    return repaired != value and len(repaired) < len(value)


def repair_referentials(apps, schema_editor):
    for model_name, fields in TARGETS:
        Model = apps.get_model("exercise", model_name)
        for obj in Model.objects.all():
            updates = {}
            for field in fields:
                value = getattr(obj, field, None)
                if _is_mojibake(value):
                    updates[field] = value.encode("latin-1").decode("utf-8")
            if updates:
                for field, fixed in updates.items():
                    setattr(obj, field, fixed)
                obj.save(update_fields=list(updates))


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("exercise", "0010_add_mmss_validator"),
    ]
    operations = [
        migrations.RunPython(repair_referentials, reverse_noop),
    ]
