from django.db import migrations


def link_energy_systems(apps, schema_editor):
    """Link the 4 existing EnergySystems to the Natation Sport.

    Pre-modeltranslation seed: a single Sport (Natation) and 4 EnergySystems
    sharing it implicitly. This migration materialises the M2M.
    """
    Sport = apps.get_model("sport", "Sport")
    EnergySystem = apps.get_model("exercise", "EnergySystem")

    natation = Sport.objects.filter(slug="natation").first()
    if natation is None:
        print("WARNING: Sport 'natation' not found, skipping data migration")
        return

    all_energy_systems = list(EnergySystem.objects.all())
    natation.energy_systems.set(all_energy_systems)
    print(f"Linked {len(all_energy_systems)} EnergySystems to Sport Natation")


def reverse_unlink(apps, schema_editor):
    Sport = apps.get_model("sport", "Sport")
    natation = Sport.objects.filter(slug="natation").first()
    if natation is not None:
        natation.energy_systems.clear()


class Migration(migrations.Migration):

    dependencies = [
        ("sport", "0002_add_energy_systems_m2m"),
        ("exercise", "0006_add_is_active"),
    ]

    operations = [
        migrations.RunPython(link_energy_systems, reverse_unlink),
    ]
