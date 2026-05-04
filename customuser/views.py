import logging

from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers as drf_serializers
from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import CustomUser
from .serializers import (
    EmailConfirmSerializer,
    EmailResendSerializer,
    MeSerializer,
    RegisterSerializer,
    VerifiedTokenObtainPairSerializer,
)

logger = logging.getLogger(__name__)


class MeView(RetrieveUpdateAPIView):
    """GET/PATCH du profil de l'utilisateur connecté.

    PUT is intentionally disabled to prevent partial bodies from resetting
    unspecified writable fields (first_name, last_name, language) to their
    defaults. Use PATCH for any update.

    `email` is read-only here; changing the email requires admin intervention
    in v1 (a verified change-email flow is deferred to v2).
    """

    serializer_class = MeSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return self.request.user


def _jwt_pair(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def _user_payload(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "language": user.language,
    }


class RegisterView(APIView):
    """POST /api/v1/auth/register/ — public self-signup.

    Creates a CustomUser (is_active=True) plus an unverified EmailAddress
    via allauth, then sends a confirmation email. No JWT is returned —
    the caller must verify their email before obtaining tokens.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(
                description=(
                    "Account created. Returns "
                    "{detail, code: 'registration_pending_verification', username, email}. "
                    "JWT is intentionally NOT returned — the user must confirm their "
                    "email first."
                )
            ),
            400: OpenApiResponse(
                description=(
                    "Validation error. Field-level codes include `username_taken`, "
                    "`email_taken`, password validators."
                )
            ),
        },
    )
    def post(self, request):
        from allauth.account.models import EmailAddress

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = CustomUser.objects.create_user(
            username=data["username"],
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            language=data.get("language", "en"),
        )
        address = EmailAddress.objects.create(
            user=user, email=user.email, primary=True, verified=False
        )
        address.send_confirmation(request, signup=True)

        return Response(
            {
                "detail": _(
                    "Account created. Please check your email to confirm your registration."
                ),
                "code": "registration_pending_verification",
                "username": user.username,
                "email": user.email,
            },
            status=status.HTTP_201_CREATED,
        )


class ConfirmEmailView(APIView):
    """POST /api/v1/auth/email/confirm/ — finalize signup with the key
    received by email. Returns JWT tokens for auto-login.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        request=EmailConfirmSerializer,
        responses={
            200: OpenApiResponse(description="Email verified. Returns {access, refresh, user}."),
            400: OpenApiResponse(
                description="Token invalid or expired. code=invalid_or_expired_token."
            ),
        },
    )
    def post(self, request):
        from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC

        serializer = EmailConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = serializer.validated_data["key"]

        # Try HMAC first (no DB row, default for ACCOUNT_EMAIL_CONFIRMATION_HMAC=True)
        confirmation = EmailConfirmationHMAC.from_key(key)
        if confirmation is None:
            # Legacy fallback for db-stored confirmations.
            try:
                confirmation = EmailConfirmation.objects.get(key=key.lower())
            except EmailConfirmation.DoesNotExist:
                confirmation = None

        if confirmation is None or confirmation.key_expired():
            raise drf_serializers.ValidationError(
                {"detail": _("Invalid or expired confirmation token.")},
                code="invalid_or_expired_token",
            )

        email_address = confirmation.confirm(request)
        if email_address is None:
            # confirm() returns None when EmailAddress no longer exists
            # or was already confirmed in a way that cancelled this key.
            raise drf_serializers.ValidationError(
                {"detail": _("Invalid or expired confirmation token.")},
                code="invalid_or_expired_token",
            )

        user = email_address.user
        return Response({**_jwt_pair(user), "user": _user_payload(user)})


class ResendEmailView(APIView):
    """POST /api/v1/auth/email/resend/ — re-send confirmation link.

    Anti-leak: always returns 200 regardless of whether the email exists,
    so an attacker cannot enumerate registered emails. The fact that no
    email is sent for unknown addresses must remain invisible to the
    client.

    TODO Batch 2: rate-limit this endpoint to prevent timing-based
    enumeration and email-spam abuse.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        request=EmailResendSerializer,
        responses={
            200: OpenApiResponse(
                description=(
                    "Always 200. Returns {detail, code: 'resend_processed'}. "
                    "If a matching unverified account exists, a new confirmation "
                    "email has been dispatched; otherwise the response is identical."
                )
            ),
            400: OpenApiResponse(description="Body validation error (e.g. malformed email)."),
        },
    )
    def post(self, request):
        from allauth.account.models import EmailAddress

        serializer = EmailResendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].lower()

        try:
            address = EmailAddress.objects.get(email__iexact=email, verified=False)
            address.send_confirmation(request)
        except EmailAddress.DoesNotExist:
            # Anti-leak: silently no-op.
            pass

        return Response(
            {
                "detail": _(
                    "If a matching unverified account exists, a confirmation email has been sent."
                ),
                "code": "resend_processed",
            }
        )


class VerifiedTokenObtainPairView(TokenObtainPairView):
    """Drop-in replacement for SimpleJWT's TokenObtainPairView that refuses
    login when the user's primary email is unverified."""

    serializer_class = VerifiedTokenObtainPairSerializer
