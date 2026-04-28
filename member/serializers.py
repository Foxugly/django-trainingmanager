from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from customuser.serializers import CustomUserPublicSerializer

from .models import Member

User = get_user_model()


class MemberSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()
    user = CustomUserPublicSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        source="user",
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

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
            "user_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "fullname", "created_at", "updated_at"]

    @extend_schema_field(serializers.CharField())
    def get_fullname(self, obj) -> str:
        parts = [p for p in [obj.firstname, obj.lastname] if p]
        return " ".join(parts) if parts else ""

    def validate(self, data):
        data = super().validate(data)
        user = data.get("user")
        teams = data.get("teams") or (list(self.instance.teams.all()) if self.instance else [])
        if user is not None and teams:
            user_team_ids = set(user.owned_teams.values_list("pk", flat=True)) | set(
                user.managed_teams.values_list("pk", flat=True)
            )
            member_profile = getattr(user, "member_profile", None)
            if member_profile is not None:
                user_team_ids |= set(member_profile.teams.values_list("pk", flat=True))
            requested_team_ids = {t.pk for t in teams}
            if user_team_ids.isdisjoint(requested_team_ids):
                raise serializers.ValidationError(
                    {
                        "user_id": _(
                            "The user must already belong to at least one of the member's teams."
                        )
                    },
                    code="user_team_mismatch",
                )
        return data
