from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from tools.exceptions import EmailNotVerified

from .models import CustomUser


class CustomUserPublicSerializer(serializers.ModelSerializer):
    """Public user payload for nested read contexts.

    Excludes email and other privacy-sensitive fields. Use this whenever
    a user is exposed inside another resource (Team.owner, Member.user,
    TeamInvitation.invited_by, ...).
    """

    class Meta:
        model = CustomUser
        fields = ["id", "username", "first_name", "last_name"]
        read_only_fields = fields


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "language",
            "last_login",
            "date_joined",
            "is_staff",
            "is_superuser",
        ]
        read_only_fields = [
            "id",
            "username",
            "email",
            "last_login",
            "date_joined",
            "is_staff",
            "is_superuser",
        ]


class RegisterSerializer(serializers.Serializer):
    """Public registration payload for POST /api/v1/auth/register/.

    Validates uniqueness against both CustomUser AND allauth.EmailAddress
    (allauth allows two unverified entries for the same email otherwise).

    `turnstile_token` is required: server-side verification with Cloudflare
    happens in the view (not here, because we need the request to extract
    the remote IP). The serializer just enforces presence."""

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    # Reuse the (code, label) tuple from settings.LANGUAGES so drf-spectacular
    # unifies this enum with CustomUser.language and avoids a "collision"
    # warning that would force a suffixed name like LanguageFd4Enum.
    language = serializers.ChoiceField(
        choices=settings.LANGUAGES,
        required=False,
        default="en",
    )
    turnstile_token = serializers.CharField(write_only=True)

    def validate_username(self, value):
        if CustomUser.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                _("This username is already taken."), code="username_taken"
            )
        return value

    def validate_email(self, value):
        from allauth.account.models import EmailAddress

        normalized = value.lower()
        if CustomUser.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError(
                _("This email is already in use."), code="email_taken"
            )
        if EmailAddress.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError(
                _("This email is already in use."), code="email_taken"
            )
        return normalized

    def validate_password(self, value):
        validate_password(value)
        return value


class EmailConfirmSerializer(serializers.Serializer):
    """Body for POST /api/v1/auth/email/confirm/."""

    key = serializers.CharField()


class EmailResendSerializer(serializers.Serializer):
    """Body for POST /api/v1/auth/email/resend/."""

    email = serializers.EmailField()


class VerifiedTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Block JWT login when the user has an unverified primary email.

    Legacy users predating allauth integration have no EmailAddress row;
    they are treated as verified to preserve backwards compatibility (no
    data migration). Once an EmailAddress exists for a user, the
    `verified` flag becomes authoritative."""

    def validate(self, attrs):
        from allauth.account.models import EmailAddress

        data = super().validate(attrs)  # raises 401 if creds invalid; sets self.user
        addresses = EmailAddress.objects.filter(user=self.user)
        if addresses.exists() and not addresses.filter(verified=True).exists():
            # Use a dedicated APIException (not ValidationError) so the
            # custom_exception_handler hits the APIException branch and
            # surfaces default_code="email_not_verified" at the top of
            # the response, exactly like ResourceLocked does.
            raise EmailNotVerified()
        return data
