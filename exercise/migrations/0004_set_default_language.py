from django.db import migrations


def set_french_default(apps, schema_editor):
    Exercise = apps.get_model("exercise", "Exercise")
    Exercise.objects.filter(language__isnull=True).update(language="fr")


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("exercise", "0003_exercise_language"),
    ]

    operations = [
        migrations.RunPython(set_french_default, reverse_noop),
    ]
