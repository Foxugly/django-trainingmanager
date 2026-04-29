from rest_framework import serializers

from .models import Note
from .sanitizer import sanitize_html


class NoteSerializer(serializers.ModelSerializer):
    """Serializer for Note. team/member/author are derived from the URL
    and the request user; they are read-only here. The 'content' field
    is sanitized via bleach on every write."""

    author_username = serializers.CharField(
        source="author.username",
        read_only=True,
        default=None,
    )

    class Meta:
        model = Note
        fields = [
            "id",
            "team",
            "member",
            "author",
            "author_username",
            "content",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "team",
            "member",
            "author",
            "author_username",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def validate_content(self, value):
        return sanitize_html(value)
