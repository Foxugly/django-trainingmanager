from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class CustomUserManager(BaseUserManager):

    def create_user(self, username, email, password):
        user = self.model(username=username, email=email, password=password)
        user.set_password(password)
        user.is_superuser = False
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password):
        user = self.model(username=username, email=email, password=password)
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class CustomUser(AbstractUser):
    language = models.CharField(_("language"), max_length=8, choices=settings.LANGUAGES, default=1)
    is_foo_admin = models.BooleanField(_("Foo admin"), default=False, help_text=_('Designates users that are foo Admin.'),)
    objects = CustomUserManager()

    USERNAME_FIELD = 'username'

    def __str__(self):
        return self.username
