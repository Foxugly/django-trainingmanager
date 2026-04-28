from django.db import migrations


def backfill_translations(apps, schema_editor):
    """Copy name -> name_fr and description -> description_fr for existing rows.

    Idempotent: skip rows already populated. Other language variants
    (nl, en, it, es) remain null and will fall back to fr at runtime.
    """
    Modality = apps.get_model("exercise", "Modality")
    EnergySystem = apps.get_model("exercise", "EnergySystem")
    EnergySegment = apps.get_model("exercise", "EnergySegment")

    m_updated = 0
    for m in Modality.objects.all():
        if not m.name_fr:
            m.name_fr = m.name
            m.save(update_fields=["name_fr"])
            m_updated += 1

    es_updated = 0
    for es in EnergySystem.objects.all():
        if not es.name_fr:
            es.name_fr = es.name
            es.save(update_fields=["name_fr"])
            es_updated += 1

    seg_updated = 0
    for seg in EnergySegment.objects.all():
        if not seg.description_fr and seg.description:
            seg.description_fr = seg.description
            seg.save(update_fields=["description_fr"])
            seg_updated += 1

    print(
        f"Backfilled translations: {m_updated} Modality.name_fr, "
        f"{es_updated} EnergySystem.name_fr, "
        f"{seg_updated} EnergySegment.description_fr"
    )


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("exercise", "0007_alter_modality_unique_together_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_translations, reverse_noop),
    ]
