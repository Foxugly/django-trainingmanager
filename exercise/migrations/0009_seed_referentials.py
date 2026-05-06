"""Seed referentials for fresh-clone bootstrap: EnergySystem, EnergySegment,
and Modality (Natation).

Replaces the historical `loaddata db.json` workflow. Idempotent (each row
is keyed on its natural unique key). Inactive/test rows from previous dev
DBs are not seeded — only canonical referentials.

Modalities are sport-scoped; this migration links them to the Natation
Sport seeded in `sport.0006_seed_default_sport`.
"""

from django.db import migrations

ENERGY_SYSTEMS = [
    {
        "name": "Relax",
        "name_fr": "Relax",
        "name_nl": "Relax",
        "name_en": "Relax",
        "name_it": "Relax",
        "name_es": "Relax",
    },
    {
        "name": "Endurance",
        "name_fr": "Endurance",
        "name_nl": "Uithouding",
        "name_en": "Endurance",
        "name_it": "Resistenza",
        "name_es": "Resistencia",
    },
    {
        "name": "Resistance",
        "name_fr": "Resistance",
        "name_nl": "Weerstand",
        "name_en": "Resistance",
        "name_it": "Resistenza",
        "name_es": "Resistencia",
    },
    {
        "name": "Sprint",
        "name_fr": "Sprint",
        "name_nl": "Sprint",
        "name_en": "Sprint",
        "name_it": "Sprint",
        "name_es": "Sprint",
    },
]

# (energysystem name, abv, optional description per language)
ENERGY_SEGMENTS = [
    ("Relax", "Z0", {}),
    ("Endurance", "Z1", {}),
    ("Endurance", "Z2", {}),
    ("Endurance", "Z3", {"description_fr": "vo2max", "description_en": "vo2max"}),
    ("Resistance", "Z4", {}),
    ("Resistance", "Z5", {}),
    ("Sprint", "Z6", {}),
    ("Sprint", "Z7", {}),
]

# Natation modalities, fully translated. fr/nl/en/it/es per the project's 5
# supported languages.
NATATION_MODALITIES = [
    ("Crawl", "Vrije slag", "Freestyle", "Stile libero", "Crol"),
    ("Brasse", "Schoolslag", "Breaststroke", "Rana", "Braza"),
    ("Dos", "Rugslag", "Backstroke", "Dorso", "Espalda"),
    ("Papillon", "Vlinderslag", "Butterfly", "Delfino", "Mariposa"),
    ("Jambes - battements", "Benen - slag", "Legs - kicks", "Gambe - battuta", "Piernas - patada"),
    (
        "Jambes - rotation",
        "Benen - rotatie",
        "Legs - egg beater",
        "Gambe - rotazione",
        "Piernas - rotación",
    ),
    (
        "Jambes - brasse",
        "Benen - schoolslag",
        "Legs - breaststroke",
        "Gambe - rana",
        "Piernas - braza",
    ),
    ("Libre", "Vrij", "Free", "Libero", "Libre"),
    ("Quatre nages", "Wisselslag", "Medley", "Misti", "Estilos"),
    ("Apnée", "Apneu", "Apnea", "Apnea", "Apnea"),
    ("Jambes - libre", "Benen - vrij", "Legs - Free", "Gambe - libero", "Piernas - libre"),
    (
        "Water-polo : passes",
        "Waterpolo : passes",
        "Water-Polo : passes",
        "Pallanuoto: passaggi",
        "Waterpolo : pases",
    ),
    (
        "Water-polo : tirs",
        "Waterpolo : schoten",
        "Water-Polo : shots",
        "Pallanuoto : tiri",
        "Waterpolo : tiros",
    ),
    ("Water-polo", "Waterpolo", "Water-Polo", "Pallanuoto", "Waterpolo"),
]


def seed_referentials(apps, schema_editor):
    EnergySystem = apps.get_model("exercise", "EnergySystem")
    EnergySegment = apps.get_model("exercise", "EnergySegment")
    Modality = apps.get_model("exercise", "Modality")
    Sport = apps.get_model("sport", "Sport")

    es_by_name = {}
    for data in ENERGY_SYSTEMS:
        obj, _ = EnergySystem.objects.update_or_create(
            name=data["name"],
            defaults={**data, "is_active": True},
        )
        es_by_name[data["name"]] = obj

    for es_name, abv, desc in ENERGY_SEGMENTS:
        EnergySegment.objects.update_or_create(
            abv=abv,
            energysystem=es_by_name[es_name],
            defaults={**desc, "is_active": True},
        )

    natation = Sport.objects.filter(slug="natation").first()
    if natation is None:
        # Sport 0006 should have created it; bail silently if not.
        return
    for fr, nl, en, it, es in NATATION_MODALITIES:
        Modality.objects.update_or_create(
            name=fr,
            sport=natation,
            defaults={
                "name_fr": fr,
                "name_nl": nl,
                "name_en": en,
                "name_it": it,
                "name_es": es,
                "is_active": True,
            },
        )


def reverse_noop(apps, schema_editor):
    # Don't auto-delete — referentials may be linked to user-created Exercises.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("exercise", "0008_backfill_translations"),
        ("sport", "0006_seed_default_sport"),
    ]
    operations = [
        migrations.RunPython(seed_referentials, reverse_noop),
    ]
