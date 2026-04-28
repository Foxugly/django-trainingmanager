from django.db import migrations


def set_french_default(apps, schema_editor):
    Round = apps.get_model("round", "Round")
    Round.objects.filter(language__isnull=True).update(language="fr")


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("round", "0006_round_language"),
    ]

    operations = [
        migrations.RunPython(set_french_default, reverse_noop),
    ]
