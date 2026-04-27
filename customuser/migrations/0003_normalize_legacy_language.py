from django.db import migrations

VALID_CODES = {"fr", "nl", "en", "it", "es"}


def normalize_language(apps, schema_editor):
    """Replace legacy language values (e.g. '1', empty string, unknown codes)
    with the project default 'fr'."""
    User = apps.get_model("customuser", "CustomUser")
    User.objects.exclude(language__in=VALID_CODES).update(language="fr")


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("customuser", "0002_alter_customuser_language"),
    ]

    operations = [
        migrations.RunPython(normalize_language, reverse_noop),
    ]
