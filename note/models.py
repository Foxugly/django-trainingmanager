from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Note(models.Model):
    """Coach note about a member within a team.

    Read access for the member depends on team.athlete_can_read_notes
    AND on the member being the user's own profile.
    """

    team = models.ForeignKey(
        "team.Team",
        on_delete=models.CASCADE,
        related_name="notes",
    )
    member = models.ForeignKey(
        "member.Member",
        on_delete=models.CASCADE,
        related_name="notes",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notes_authored",
        help_text=_("The coach who wrote this note. SET_NULL if the author account is deleted."),
    )
    content = models.TextField(
        help_text=_("Rich HTML content (sanitized via bleach on save)."),
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["team", "member", "is_active", "-created_at"],
                name="note_team_member_active_idx",
            ),
        ]

    def __str__(self):
        author_str = self.author.username if self.author else "(deleted)"
        return f"Note by {author_str} on {self.member} ({self.created_at:%Y-%m-%d})"
