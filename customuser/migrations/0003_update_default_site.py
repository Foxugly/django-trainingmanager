from django.db import migrations


def update_site(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.update_or_create(
        pk=1,
        defaults={'domain': 'localhost:8000', 'name': 'TrainingManager'},
    )


def reverse_update_site(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('customuser', '0002_alter_customuser_id'),
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        migrations.RunPython(update_site, reverse_update_site),
    ]
