from django.db import migrations


def backfill_name_fr(apps, schema_editor):
    """Copy Sport.name into Sport.name_fr for existing rows.

    Idempotent: skip rows where name_fr is already populated. Other
    language variants (nl, en, it, es) are left null on purpose —
    they will be filled by translators later, with FR as fallback.
    """
    Sport = apps.get_model("sport", "Sport")
    updated = 0
    for sport in Sport.objects.all():
        if not sport.name_fr:
            sport.name_fr = sport.name
            sport.save(update_fields=["name_fr"])
            updated += 1
    print(f"Backfilled {updated} Sport.name_fr (out of {Sport.objects.count()})")


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("sport", "0004_sport_name_en_sport_name_es_sport_name_fr_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_name_fr, reverse_noop),
    ]
