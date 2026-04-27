from django.db import migrations


def set_sport_from_exercises(apps, schema_editor):
    """Derive Round.sport from the modality.sport of its exercises.

    - 1 sport in exercises -> assign that sport
    - 0 exercises (empty round) -> assign 'natation' (project default)
    - mixed sports -> assign 'natation' and surface a warning
    """
    Round = apps.get_model("round", "Round")
    Sport = apps.get_model("sport", "Sport")

    natation = Sport.objects.filter(slug="natation").first()
    if natation is None:
        # Fallback: pick any sport — install must have at least one
        natation = Sport.objects.first()
    if natation is None:
        # Empty Sport table: nothing to migrate; the next NOT-NULL migration
        # will fail loudly anyway.
        return

    for r in Round.objects.filter(sport__isnull=True):
        sport_ids = list(r.exercises.values_list("modality__sport_id", flat=True).distinct())
        sport_ids = [s for s in sport_ids if s is not None]

        if len(sport_ids) == 1:
            r.sport_id = sport_ids[0]
        elif len(sport_ids) == 0:
            r.sport = natation
        else:
            print(
                f"WARNING: Round#{r.pk} has mixed exercise sports {sport_ids}, "
                f"defaulting to {natation.slug}"
            )
            r.sport = natation
        r.save(update_fields=["sport"])

    remaining = Round.objects.filter(sport__isnull=True).count()
    if remaining > 0:
        raise Exception(f"{remaining} Rounds still have NULL sport after data migration")


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("round", "0003_round_sport"),
        ("sport", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(set_sport_from_exercises, reverse_noop),
    ]
