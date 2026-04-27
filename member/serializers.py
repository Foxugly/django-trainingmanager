from rest_framework import serializers

from .models import Member


class MemberSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = [
            "id",
            "firstname",
            "lastname",
            "fullname",
            "email",
            "phonenumber",
            "teams",
            "user",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "fullname", "created_at", "updated_at"]

    def get_fullname(self, obj):
        parts = [p for p in [obj.firstname, obj.lastname] if p]
        return " ".join(parts) if parts else ""
