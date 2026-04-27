import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


def generate_invitation_token():
    return secrets.token_urlsafe(32)


def default_invitation_expiration():
    return timezone.now() + timedelta(days=7)


class Team(models.Model):
    name = models.CharField(max_length=200, unique=True)
    sport = models.ForeignKey(
        "sport.Sport",
        on_delete=models.PROTECT,
        related_name="teams",
        null=True,
        blank=True,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_teams",
    )
    managers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="managed_teams",
        blank=True,
    )
    language = models.CharField(
        max_length=2,
        choices=settings.LANGUAGES,
        default="fr",
    )
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def is_managed_by(self, user):
        if not user.is_authenticated:
            return False
        return user == self.owner or self.managers.filter(pk=user.pk).exists()


class TeamJoinRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="join_requests",
    )
    team = models.ForeignKey(
        "team.Team",
        on_delete=models.CASCADE,
        related_name="join_requests",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    message = models.TextField(blank=True)
    response_message = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="handled_join_requests",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-requested_at"]

    def __str__(self):
        return f"{self.user} -> {self.team} ({self.status})"


class TeamInvitation(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    ]

    team = models.ForeignKey(
        "team.Team",
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_invitations",
    )
    member = models.OneToOneField(
        "member.Member",
        on_delete=models.CASCADE,
        related_name="invitation",
    )
    email = models.EmailField()
    token = models.CharField(
        max_length=64,
        unique=True,
        default=generate_invitation_token,
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_invitation_expiration)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invitation to {self.team.name} for {self.email} ({self.status})"

    def is_valid(self):
        if self.status != "pending":
            return False
        if timezone.now() > self.expires_at:
            return False
        return True
