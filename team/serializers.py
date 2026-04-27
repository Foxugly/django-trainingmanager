from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Team, TeamInvitation, TeamJoinRequest


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = [
            "id",
            "name",
            "sport",
            "owner",
            "managers",
            "is_active",
            "is_public",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]
        extra_kwargs = {
            "sport": {"required": True, "allow_null": False},
        }


class TeamJoinRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamJoinRequest
        fields = [
            "id",
            "user",
            "team",
            "status",
            "message",
            "response_message",
            "requested_at",
            "responded_at",
            "responded_by",
        ]
        read_only_fields = [
            "id",
            "user",
            "requested_at",
            "responded_at",
            "responded_by",
        ]


class CreateJoinRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamJoinRequest
        fields = ["id", "team", "message"]
        read_only_fields = ["id"]

    def validate(self, data):
        user = self.context["request"].user
        team = data["team"]
        member_profile = getattr(user, "member_profile", None)
        if member_profile is not None and member_profile.teams.filter(pk=team.pk).exists():
            raise serializers.ValidationError({"team": "Vous etes deja membre de cette team."})
        if TeamJoinRequest.objects.filter(user=user, team=team, status="pending").exists():
            raise serializers.ValidationError(
                {"team": "Vous avez deja une demande en attente pour cette team."}
            )
        if not team.is_active:
            raise serializers.ValidationError({"team": "Cette team est inactive."})
        if not team.is_public:
            raise serializers.ValidationError({"team": "Cette team n'est pas publique."})
        return data


class TeamInvitationSerializer(serializers.ModelSerializer):
    """List/detail view for managers. Token is intentionally excluded."""

    class Meta:
        model = TeamInvitation
        fields = [
            "id",
            "team",
            "invited_by",
            "member",
            "email",
            "status",
            "created_at",
            "expires_at",
            "completed_at",
        ]
        read_only_fields = [
            "id",
            "invited_by",
            "member",
            "status",
            "created_at",
            "expires_at",
            "completed_at",
        ]


class CreateInvitationSerializer(serializers.Serializer):
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    email = serializers.EmailField()
    firstname = serializers.CharField(max_length=100)
    lastname = serializers.CharField(max_length=100)
    phonenumber = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")

    def validate_team(self, team):
        user = self.context["request"].user
        if not team.is_managed_by(user):
            raise serializers.ValidationError("Vous ne gerez pas cette team.")
        if not team.is_active:
            raise serializers.ValidationError("Cette team est inactive.")
        return team

    def validate(self, data):
        if TeamInvitation.objects.filter(
            email=data["email"],
            team=data["team"],
            status="pending",
        ).exists():
            raise serializers.ValidationError(
                {"email": "Une invitation est deja en cours pour cet email sur cette team."}
            )
        return data


class ValidateInvitationSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source="team.name", read_only=True)

    class Meta:
        model = TeamInvitation
        fields = ["email", "team_name", "status", "expires_at"]
        read_only_fields = fields


class CompleteInvitationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_username(self, username):
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est deja pris.")
        return username

    def validate_password(self, password):
        from django.contrib.auth.password_validation import validate_password

        validate_password(password)
        return password
