from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from tools.html_sanitizer import sanitize_html

from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    """Message serializer with author username for display."""

    author_username = serializers.CharField(
        source="author.username",
        read_only=True,
        default=None,
    )

    class Meta:
        model = Message
        fields = [
            "id",
            "team",
            "author",
            "author_username",
            "content",
            "created_at",
            "edited_at",
            "deleted_at",
        ]
        read_only_fields = [
            "id",
            "team",
            "author",
            "author_username",
            "created_at",
            "edited_at",
            "deleted_at",
        ]

    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                _("Message content cannot be empty."),
                code="empty_content",
            )
        cleaned = sanitize_html(value)
        if not cleaned or not cleaned.strip():
            # Sanitization may have stripped everything (only disallowed tags)
            raise serializers.ValidationError(
                _("Message content cannot be empty."),
                code="empty_content",
            )
        return cleaned
