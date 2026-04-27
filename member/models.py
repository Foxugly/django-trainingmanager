from django.conf import settings
from django.db import models
from django.utils.translation import gettext as _

from tools.generic_class import GenericClass


class Member(GenericClass):
    firstname = models.CharField(max_length=100, verbose_name=_("Firstname"), )
    lastname = models.CharField(max_length=100, verbose_name=_("Lastname"), )
    phonenumber = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Phonenumber"), )
    email = models.EmailField(max_length=50, blank=True, null=True, verbose_name=_("Email"), )
    teams = models.ManyToManyField(
        'team.Team',
        related_name='members',
        blank=True,
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='member_profile',
        null=True, blank=True,
    )

    def get_fullname(self):
        return "%s %s" % (self.firstname, self.lastname)

    def __str__(self):
        return self.get_fullname()

    class Meta:
        verbose_name = _('Member')
