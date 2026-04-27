import secrets

from django.contrib.auth.hashers import make_password
from django.db import migrations
from django.utils.text import slugify


def bootstrap(apps, schema_editor):
    Team = apps.get_model('team', 'Team')
    User = apps.get_model('customuser', 'CustomUser')
    Agenda = apps.get_model('agenda', 'Agenda')
    Member = apps.get_model('member', 'Member')
    EmailAddress = apps.get_model('account', 'EmailAddress')

    try:
        owner = User.objects.get(username='renaud')
    except User.DoesNotExist:
        owner = User.objects.filter(is_superuser=True).order_by('pk').first()
    if not owner:
        return

    team, _ = Team.objects.update_or_create(
        name='RBP WP senior',
        defaults={'owner': owner, 'is_active': True, 'is_public': True},
    )

    Agenda.objects.filter(team__isnull=True).update(team=team)

    existing_emails = set(
        User.objects.exclude(email='').values_list('email', flat=True)
    )

    for m in Member.objects.all():
        m.teams.add(team)

        if not m.email:
            continue
        if m.email in existing_emails:
            continue

        base_username = slugify(f"{m.firstname}.{m.lastname}").replace('-', '.')
        if not base_username:
            continue
        username = base_username
        suffix = 2
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{suffix}"
            suffix += 1

        random_pw = secrets.token_urlsafe(20)

        user = User.objects.create(
            username=username,
            email=m.email,
            first_name=m.firstname,
            last_name=m.lastname,
            is_active=True,
            password=make_password(random_pw),
        )

        EmailAddress.objects.create(
            user=user,
            email=m.email,
            verified=True,
            primary=True,
        )

        existing_emails.add(m.email)

        m.user = user
        m.save()


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('team', '0001_initial'),
        ('agenda', '0004_agenda_team'),
        ('member', '0003_member_teams_member_user'),
        ('customuser', '0004_remove_customuser_is_foo_admin'),
        ('account', '0009_emailaddress_unique_primary_email'),
    ]

    operations = [
        migrations.RunPython(bootstrap, reverse),
    ]
