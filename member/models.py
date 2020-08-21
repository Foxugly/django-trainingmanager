from tools.generic_class import GenericClass
from django.db import models
from django.utils.translation import gettext as _


# Create your models here.
class Member(GenericClass):
    firstname = models.CharField(max_length=100, verbose_name=_("Firstname"), )
    lastname = models.CharField(max_length=100, verbose_name=_("Lastname"), )

    def get_fullname(self):
    	return "%s %s" % (self.firstname, self.lastname)

    def __str__(self):
        return self.get_fullname()

    class Meta:
        verbose_name = _('Member')