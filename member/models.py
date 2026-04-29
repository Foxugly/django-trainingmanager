from django.conf import settings
from django.db import models
from django.utils.translation import gettext as _


class Member(models.Model):
    firstname = models.CharField(
        max_length=100,
        verbose_name=_("Firstname"),
    )
    lastname = models.CharField(
        max_length=100,
        verbose_name=_("Lastname"),
    )
    phonenumber = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Phonenumber"),
    )
    email = models.EmailField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_("Email"),
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="member_profile",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_fullname(self):
        return "%s %s" % (self.firstname, self.lastname)

    def __str__(self):
        return self.get_fullname()

    @property
    def teams_active(self):
        """Team queryset for currently active memberships (left_at IS NULL)."""
        from team.models import Team

        team_ids = self.memberships.filter(left_at__isnull=True).values_list("team_id", flat=True)
        return Team.objects.filter(pk__in=team_ids)

    class Meta:
        verbose_name = _("Member")
