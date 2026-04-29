from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from customuser.serializers import CustomUserPublicSerializer
from sport.models import Sport
from sport.serializers import SportSerializer

from .models import Team, TeamInvitation, TeamJoinRequest, TeamMembership


class TeamMinimalSerializer(serializers.ModelSerializer):
    """Compact team payload for nested read contexts."""

    class Meta:
        model = Team
        fields = ["id", "name", "language"]
        read_only_fields = fields


class TeamSerializer(serializers.ModelSerializer):
    sport = SportSerializer(read_only=True)
    sport_id = serializers.PrimaryKeyRelatedField(
        source="sport",
        queryset=Sport.objects.all(),
        write_only=True,
    )
    owner = CustomUserPublicSerializer(read_only=True)
    managers = CustomUserPublicSerializer(many=True, read_only=True)
    managers_ids = serializers.PrimaryKeyRelatedField(
        source="managers",
        queryset=get_user_model().objects.all(),
        many=True,
        write_only=True,
        required=False,
    )

    class Meta:
        model = Team
        fields = [
            "id",
            "name",
            "sport",
            "sport_id",
            "owner",
            "managers",
            "managers_ids",
            "language",
            "is_active",
            "is_public",
            "chat_mode",
            "athlete_can_read_notes",
            "attendance_statuses",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "managers", "created_at", "updated_at"]


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
        if (
            member_profile is not None
            and member_profile.memberships.filter(team=team, left_at__isnull=True).exists()
        ):
            raise serializers.ValidationError(
                {"team": _("You are already a member of this team.")},
                code="already_member",
            )
        if TeamJoinRequest.objects.filter(user=user, team=team, status="pending").exists():
            raise serializers.ValidationError(
                {"team": _("You already have a pending request for this team.")},
                code="pending_request_exists",
            )
        if not team.is_active:
            raise serializers.ValidationError(
                {"team": _("This team is inactive.")},
                code="team_not_active",
            )
        if not team.is_public:
            raise serializers.ValidationError(
                {"team": _("This team is not public.")},
                code="team_not_public",
            )
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
            raise serializers.ValidationError(
                _("You do not manage this team."),
                code="not_a_manager",
            )
        if not team.is_active:
            raise serializers.ValidationError(
                _("This team is inactive."),
                code="team_not_active",
            )
        return team

    def validate(self, data):
        if TeamInvitation.objects.filter(
            email=data["email"],
            team=data["team"],
            status="pending",
        ).exists():
            raise serializers.ValidationError(
                {"email": _("An invitation is already pending for this email on this team.")},
                code="email_already_invited",
            )
        return data


class ValidateInvitationSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source="team.name", read_only=True)

    class Meta:
        model = TeamInvitation
        fields = ["email", "team_name", "status", "expires_at"]
        read_only_fields = fields


class TeamMembershipSerializer(serializers.ModelSerializer):
    """Read/write serializer for TeamMembership.

    `team` is set by the view from URL kwargs; only `member` is accepted on POST.
    """

    member_username = serializers.CharField(
        source="member.user.username",
        read_only=True,
        default=None,
    )
    member_fullname = serializers.SerializerMethodField()

    class Meta:
        model = TeamMembership
        fields = [
            "id",
            "team",
            "member",
            "member_username",
            "member_fullname",
            "joined_at",
            "left_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "team",
            "joined_at",
            "left_at",
            "created_at",
            "updated_at",
            "member_username",
            "member_fullname",
        ]

    @extend_schema_field(serializers.CharField())
    def get_member_fullname(self, obj) -> str:
        m = obj.member
        parts = [p for p in [m.firstname, m.lastname] if p]
        return " ".join(parts) if parts else ""


class CompleteInvitationSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_username(self, username):
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                _("This username is already taken."),
                code="username_taken",
            )
        return username

    def validate_password(self, password):
        from django.contrib.auth.password_validation import validate_password

        validate_password(password)
        return password
