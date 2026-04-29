from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Message(models.Model):
    """Team chat message. Rich HTML content sanitized on save.

    Soft delete via deleted_at (nullable timestamp). Edits tracked
    via edited_at.
    """

    team = models.ForeignKey(
        "team.Team",
        on_delete=models.CASCADE,
        related_name="messages",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="messages_authored",
        help_text=_("Author of the message. SET_NULL on user deletion."),
    )
    content = models.TextField(
        help_text=_("Rich HTML content (sanitized via bleach on save)."),
    )
    edited_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Set when the message is edited after creation."),
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Soft delete timestamp. Non-null = deleted."),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["team", "deleted_at", "-created_at"],
                name="msg_team_deleted_created_idx",
            ),
        ]

    def __str__(self):
        author_str = self.author.username if self.author else "(deleted)"
        flags = ""
        if self.edited_at:
            flags += " [edited]"
        if self.deleted_at:
            flags += " [deleted]"
        return f"Message #{self.pk} by {author_str}{flags}"

    @property
    def is_deleted(self):
        return self.deleted_at is not None
