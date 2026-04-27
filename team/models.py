from django.conf import settings
from django.db import models


class Team(models.Model):
    name = models.CharField(max_length=200, unique=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='owned_teams',
    )
    managers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='managed_teams',
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def is_managed_by(self, user):
        if not user.is_authenticated:
            return False
        return user == self.owner or self.managers.filter(pk=user.pk).exists()
