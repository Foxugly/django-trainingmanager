import logging

from django.conf import settings as dj_settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers as drf_serializers
from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from tools.openapi import INCLUDE_INACTIVE_PARAM

from .models import Team, TeamInvitation, TeamJoinRequest, TeamMembership
from .permissions import (
    IsJoinRequestParticipant,
    IsTeamManagerOrReadOnly,
    IsTrainer,
)
from .queries import managed_teams, user_visible_teams
from .serializers import (
    CompleteInvitationSerializer,
    CreateInvitationSerializer,
    CreateJoinRequestSerializer,
    JoinMagicCancelledResponseSerializer,
    JoinMagicErrorSerializer,
    TeamInvitationSerializer,
    TeamJoinRequestMagicActionPostSerializer,
    TeamJoinRequestMagicActionResponseSerializer,
    TeamJoinRequestSerializer,
    TeamMembershipSerializer,
    TeamSerializer,
    ValidateInvitationSerializer,
)

logger = logging.getLogger(__name__)


class TeamViewSet(viewsets.ModelViewSet):
    """CRUD sur Teams. Liste = teams gérées par l'user + teams publiques actives."""

    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated, IsTeamManagerOrReadOnly]
    filterset_fields = ["is_active", "is_public", "language"]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Team.objects.none()
        return (
            user_visible_teams(self.request.user)
            .select_related("sport", "owner")
            .prefetch_related("managers")
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TeamJoinRequestViewSet(viewsets.ModelViewSet):
    """Self-signup join request flow."""

    permission_classes = [IsAuthenticated, IsJoinRequestParticipant]
    filterset_fields = ["status", "team"]
    ordering_fields = ["requested_at", "responded_at"]
    ordering = ["-requested_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateJoinRequestSerializer
        return TeamJoinRequestSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return TeamJoinRequest.objects.none()
        user = self.request.user
        return TeamJoinRequest.objects.filter(
            Q(user=user) | Q(team__in=managed_teams(user))
        ).distinct()

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)

        # Auto-accept policy: short-circuit the manual flow.
        if instance.team.join_request_policy == Team.JoinRequestPolicy.AUTO:
            instance.status = "accepted"
            instance.responded_at = timezone.now()
            instance.responded_by = None  # accepted by policy, not by a person
            instance.save(update_fields=["status", "responded_at", "responded_by"])
            self._handle_acceptance(instance)
            return

        # Manual policy + opt-in notification: send email with magic links.
        if instance.team.notify_managers_on_join_request:
            self._notify_managers(instance)

    def _notify_managers(self, join_request):
        from .magic_action import magic_link

        team = join_request.team
        # Owner can also be a manager — dedupe so they don't get the email twice.
        recipients = sorted(
            {e for e in team.managers.values_list("email", flat=True) if e}
            | ({team.owner.email} if team.owner.email else set())
        )
        if not recipients:
            return
        accept_url = magic_link(join_request.id, "accept")
        reject_url = magic_link(join_request.id, "reject")
        subject = f"[TrainingManager] {_('Join request from')} {join_request.user.username}"
        body = (
            f"{join_request.user.username} ({join_request.user.email}) "
            f'{_("wants to join your team")} "{team.name}".\n\n'
            f"{_('Message')}: {join_request.message or _('(none)')}\n\n"
            f"{_('Accept')}: {accept_url}\n"
            f"{_('Reject')}: {reject_url}\n\n"
            f"{_('Links are valid for 7 days. You can also respond from the team dashboard.')}"
        )
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=dj_settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False,
            )
        except Exception:
            logger.exception("Failed to send join request notification email")

    def perform_update(self, serializer):
        instance = serializer.instance
        new_status = serializer.validated_data.get("status", instance.status)

        if new_status == instance.status:
            serializer.save()
            return

        if instance.status != "pending":
            raise drf_serializers.ValidationError(
                {"status": _("This request has already been handled.")},
                code="request_already_handled",
            )

        if new_status == "cancelled":
            if instance.user_id != self.request.user.pk:
                raise drf_serializers.ValidationError(
                    {"status": _("Only the requester can cancel this request.")},
                    code="only_owner_can_cancel",
                )
            serializer.save(responded_at=timezone.now())
            return

        if new_status in ("accepted", "rejected"):
            if not instance.team.is_managed_by(self.request.user):
                raise drf_serializers.ValidationError(
                    {"status": _("Only a manager can accept or reject this request.")},
                    code="only_manager_can_respond",
                )
            saved = serializer.save(
                responded_at=timezone.now(),
                responded_by=self.request.user,
            )
            if new_status == "accepted":
                self._handle_acceptance(saved)
            return

        raise drf_serializers.ValidationError(
            {"status": _("Unauthorized status transition.")},
            code="invalid_status_transition",
        )

    @staticmethod
    def _handle_acceptance(join_request):
        from member.models import Member

        user = join_request.user
        team = join_request.team

        existing_member = getattr(user, "member_profile", None)
        if existing_member is not None:
            if not TeamMembership.objects.filter(
                team=team, member=existing_member, left_at__isnull=True
            ).exists():
                TeamMembership.objects.create(team=team, member=existing_member)
            return

        member = Member.objects.create(
            firstname=user.first_name or user.username,
            lastname=user.last_name or "",
            email=user.email,
            phonenumber="",
            user=user,
        )
        TeamMembership.objects.create(team=team, member=member)

    @staticmethod
    def _revoke_membership(join_request):
        """Reverse a previous acceptance — used when a manager flips the
        decision via magic link from accepted -> rejected. Sets left_at on
        the active TeamMembership for (team, requester); does not delete."""
        member = getattr(join_request.user, "member_profile", None)
        if member is None:
            return
        TeamMembership.objects.filter(
            team=join_request.team,
            member=member,
            left_at__isnull=True,
        ).update(left_at=timezone.now())


class _MagicActionBase(APIView):
    """Shared behaviour for the magic-action preview (GET) and execute (POST)
    endpoints. Split into two concrete views so each only exposes the
    relevant HTTP method (avoids drf-spectacular operationId collisions)."""

    permission_classes = [IsAuthenticated]

    def _resolve(self, token):
        from .magic_action import parse_token

        parsed = parse_token(token)
        if parsed is None:
            raise drf_serializers.ValidationError(
                {"detail": _("Invalid or expired magic-action token.")},
                code="invalid_or_expired_token",
            )
        jr_id, action = parsed
        join_request = get_object_or_404(TeamJoinRequest, pk=jr_id)
        if not join_request.team.is_managed_by(self.request.user):
            raise PermissionDenied(_("You are not a manager of this team."))
        return join_request, action

    def _serialize(self, join_request, action_proposed, previous_status=None):
        """Build the magic-action response payload.

        If `previous_status` is given (POST execute path), `would_change_decision`
        reflects whether the executed action reversed a previous decision —
        otherwise (GET preview path) it predicts whether the proposed action
        WOULD reverse the current state."""
        responded_by = join_request.responded_by.username if join_request.responded_by else None
        target_status = "accepted" if action_proposed == "accept" else "rejected"
        if previous_status is None:
            # GET preview: compare against current state.
            would_change = (join_request.status == "accepted" and action_proposed == "reject") or (
                join_request.status == "rejected" and action_proposed == "accept"
            )
        else:
            # POST execute: compare the new state against what it was before.
            would_change = previous_status in ("accepted", "rejected") and (
                previous_status != target_status
            )
        return {
            "join_request": {
                "id": join_request.id,
                "team_id": join_request.team_id,
                "team_name": join_request.team.name,
                "requester_username": join_request.user.username,
                "requester_email": join_request.user.email,
                "message": join_request.message,
                "requested_at": join_request.requested_at.isoformat(),
                "status": join_request.status,
                "responded_at": (
                    join_request.responded_at.isoformat() if join_request.responded_at else None
                ),
                "responded_by": responded_by,
            },
            "action_proposed": action_proposed,
            "would_change_decision": would_change,
            "can_act": join_request.status != "cancelled",
        }


class TeamJoinRequestMagicActionPreviewView(_MagicActionBase):
    """GET /api/v1/join-magic/<token>/ — preview only. No state change.

    Safe for email link previewers (Outlook safe-links, Gmail bots).
    Returns the join request + action proposed by the token + current
    status + whether the action would reverse a previous decision +
    whether the action can still be performed (false if cancelled)."""

    @extend_schema(
        responses={
            200: TeamJoinRequestMagicActionResponseSerializer,
            400: OpenApiResponse(
                response=JoinMagicErrorSerializer,
                description="Invalid or expired token (code=invalid_or_expired_token).",
            ),
            403: OpenApiResponse(description="Not a manager of this team."),
            404: OpenApiResponse(description="Join request not found."),
        }
    )
    def get(self, request, token):
        join_request, action = self._resolve(token)
        return Response(self._serialize(join_request, action))


class TeamJoinRequestMagicActionExecuteView(_MagicActionBase):
    """POST /api/v1/join-magic/ {token} — executes the encoded action.

    Reversal support (E-b semantic):
      - pending  + accept -> accepted (creates TeamMembership)
      - pending  + reject -> rejected (no membership)
      - accepted + reject -> rejected (revokes membership: sets left_at)
      - rejected + accept -> accepted (creates membership again)
      - cancelled + *    -> 409 conflict (requester withdrew, irreversible)
    responded_by is updated to the manager who made the latest call.
    Idempotent when the request is already in the target status."""

    @extend_schema(
        request=TeamJoinRequestMagicActionPostSerializer,
        responses={
            200: OpenApiResponse(
                response=TeamJoinRequestMagicActionResponseSerializer,
                description=(
                    "Action executed (or no-op if already in target status). "
                    "Returns the same payload shape as the preview, with "
                    "the join_request reflecting the new status."
                ),
            ),
            400: OpenApiResponse(
                response=JoinMagicErrorSerializer,
                description=(
                    "Invalid or expired token (code=invalid_or_expired_token), "
                    "or missing token in body (code=token_required)."
                ),
            ),
            403: OpenApiResponse(description="Not a manager of this team."),
            404: OpenApiResponse(description="Join request not found."),
            409: OpenApiResponse(
                response=JoinMagicCancelledResponseSerializer,
                description=(
                    "Conflict: the request was cancelled by the requester and "
                    "cannot be revived (code=request_cancelled). The body still "
                    "contains the regular response payload alongside code/detail "
                    "so the frontend can show context."
                ),
            ),
        },
    )
    def post(self, request):
        token = request.data.get("token")
        if not token:
            # Pass the code via the {detail, code} dict shape so
            # custom_exception_handler surfaces it at the top level
            # ({"code": "token_required", "detail": "..."}). The {"token":
            # ...} shape would have buried the code under fields.token[0].
            raise drf_serializers.ValidationError(
                {"detail": _("token is required.")}, code="token_required"
            )
        join_request, action = self._resolve(token)
        target_status = "accepted" if action == "accept" else "rejected"

        if join_request.status == "cancelled":
            return Response(
                {
                    "code": "request_cancelled",
                    "detail": _(
                        "This join request was cancelled by the requester and cannot be acted on."
                    ),
                    **self._serialize(join_request, action),
                },
                status=status.HTTP_409_CONFLICT,
            )

        if join_request.status == target_status:
            # Idempotent: nothing to do, but report the current state so the
            # frontend can show "already X by Y on Z".
            return Response(self._serialize(join_request, action))

        previous_status = join_request.status

        with transaction.atomic():
            join_request.status = target_status
            join_request.responded_at = timezone.now()
            join_request.responded_by = request.user
            join_request.save(update_fields=["status", "responded_at", "responded_by"])
            if target_status == "accepted":
                TeamJoinRequestViewSet._handle_acceptance(join_request)
            elif previous_status == "accepted":
                TeamJoinRequestViewSet._revoke_membership(join_request)

        return Response(self._serialize(join_request, action, previous_status=previous_status))


class TeamInvitationViewSet(viewsets.ModelViewSet):
    """Trainer invitation flow."""

    permission_classes = [IsAuthenticated, IsTrainer]
    filterset_fields = ["status", "team"]
    ordering_fields = ["created_at", "expires_at"]
    ordering = ["-created_at"]
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateInvitationSerializer
        return TeamInvitationSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return TeamInvitation.objects.none()
        user = self.request.user
        return TeamInvitation.objects.filter(team__in=managed_teams(user)).distinct()

    @extend_schema(
        request=CreateInvitationSerializer,
        responses={
            201: TeamInvitationSerializer,
            400: OpenApiResponse(
                description=(
                    "Validation error. Possible codes include: "
                    "`user_already_registered` when the email matches an existing "
                    "user account (direct enrolment is refused for existing users); "
                    "`email_already_invited`, `not_a_manager`, `team_not_active`."
                ),
            ),
        },
        description=(
            "Trainer pre-registers an athlete on a managed team by sending an "
            "invitation email. Refused with code=user_already_registered if the "
            "email matches an existing user account; the trainer must use a "
            "different flow (e.g. ask the user to issue a TeamJoinRequest) for "
            "registered users."
        ),
    )
    def create(self, request, *args, **kwargs):
        from member.models import Member

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        User = get_user_model()
        if User.objects.filter(email=data["email"]).exists():
            raise drf_serializers.ValidationError(
                {
                    "detail": _(
                        "Cet utilisateur est déjà enregistré. Une invitation "
                        "directe n'est pas possible pour les comptes existants."
                    ),
                },
                code="user_already_registered",
            )

        member = Member.objects.create(
            firstname=data["firstname"],
            lastname=data["lastname"],
            email=data["email"],
            phonenumber=data.get("phonenumber", ""),
        )
        invitation = TeamInvitation.objects.create(
            team=data["team"],
            invited_by=request.user,
            member=member,
            email=data["email"],
        )
        self._send_invitation_email(invitation)
        return Response(
            TeamInvitationSerializer(invitation, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    def _send_invitation_email(self, invitation):
        frontend_url = dj_settings.FRONTEND_URL.rstrip("/")
        link = f"{frontend_url}/invitation/{invitation.token}"
        subject = f"[TrainingManager] Vous etes invite dans {invitation.team.name}"
        body = (
            f"Bonjour {invitation.member.firstname},\n\n"
            f"{invitation.invited_by.username} vous a invite a rejoindre "
            f'la team "{invitation.team.name}".\n\n'
            f"Pour finaliser votre inscription, cliquez sur ce lien :\n"
            f"{link}\n\n"
            f"Le lien est valable jusqu'au {invitation.expires_at.strftime('%d/%m/%Y')}.\n"
        )
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=dj_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[invitation.email],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Failed to send invitation email")

    def perform_destroy(self, instance):
        if instance.status != "pending":
            raise drf_serializers.ValidationError(
                {"detail": _("Only pending invitations can be cancelled.")},
                code="invitation_pending_required",
            )
        instance.status = "cancelled"
        instance.save()


class InvitationLookupView(APIView):
    """Public endpoint to validate and finalize an invitation token."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        responses={
            200: ValidateInvitationSerializer,
            400: OpenApiResponse(description="Invitation not pending (already handled)"),
            404: OpenApiResponse(description="Token not found"),
            410: OpenApiResponse(description="Invitation expired"),
        },
        description="Lookup an invitation by token. No authentication required.",
    )
    def get(self, request, token):
        invitation = get_object_or_404(TeamInvitation, token=token)
        if not invitation.is_valid():
            if invitation.status == "pending" and timezone.now() > invitation.expires_at:
                invitation.status = "expired"
                invitation.save()
                return Response(
                    {"code": "invitation_expired", "detail": _("Invitation expired.")},
                    status=status.HTTP_410_GONE,
                )
            return Response(
                {
                    "code": f"invitation_{invitation.status}",
                    "detail": _("Invitation is not pending."),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(ValidateInvitationSerializer(invitation).data)

    @extend_schema(
        request=CompleteInvitationSerializer,
        responses={
            201: OpenApiResponse(
                response=inline_serializer(
                    name="CompleteInvitationResponse",
                    fields={
                        "detail": drf_serializers.CharField(),
                        "username": drf_serializers.CharField(),
                        "access": drf_serializers.CharField(),
                        "refresh": drf_serializers.CharField(),
                    },
                ),
                description="User created and JWT issued",
            ),
            400: OpenApiResponse(
                description="Invalid token state, username taken, or weak password"
            ),
            404: OpenApiResponse(description="Token not found"),
        },
        description="Finalize invitation: create the user, link Member, return JWT.",
    )
    def post(self, request, token):
        from allauth.account.models import EmailAddress
        from rest_framework_simplejwt.tokens import RefreshToken

        invitation = get_object_or_404(TeamInvitation, token=token)
        if not invitation.is_valid():
            return Response(
                {
                    "code": f"invitation_{invitation.status}",
                    "detail": _("Invitation is not pending."),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CompleteInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        User = get_user_model()
        with transaction.atomic():
            user = User.objects.create_user(
                username=serializer.validated_data["username"],
                email=invitation.email,
                password=serializer.validated_data["password"],
                first_name=invitation.member.firstname,
                last_name=invitation.member.lastname,
                is_active=True,
            )
            EmailAddress.objects.create(
                user=user,
                email=invitation.email,
                verified=True,
                primary=True,
            )
            invitation.member.user = user
            invitation.member.save()

            invitation.status = "completed"
            invitation.completed_at = timezone.now()
            invitation.save()

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "detail": _("Account created and invitation finalized."),
                "username": user.username,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(parameters=[INCLUDE_INACTIVE_PARAM])
class TeamMembershipViewSet(viewsets.ModelViewSet):
    """Manage team memberships.

    URL: /api/v1/teams/{team_pk}/memberships/

    - GET (list): active memberships of the team. Pass ?include_inactive=true
      to also see historical (left_at IS NOT NULL) rows.
    - POST: add a member to the team (manager-only). Idempotent: rejects with
      400 already_member if an active membership already exists for the same
      (team, member) pair.
    - DELETE /{id}/: end a membership (sets left_at = now). Allowed for the
      member herself or a team manager. The team owner cannot leave their own
      team via this endpoint.
    """

    serializer_class = TeamMembershipSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_team(self):
        team_pk = self.kwargs.get("team_pk")
        if not team_pk:
            return None
        return get_object_or_404(Team, pk=team_pk)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return TeamMembership.objects.none()

        team = self.get_team()
        if team is None:
            return TeamMembership.objects.none()

        user = self.request.user
        is_team_member = (
            team.is_managed_by(user)
            or team.memberships.filter(member__user_id=user.pk, left_at__isnull=True).exists()
        )
        if not is_team_member:
            return TeamMembership.objects.none()

        qs = TeamMembership.objects.filter(team=team).select_related("member", "member__user")

        if self.action == "list":
            include_inactive = self.request.query_params.get("include_inactive") == "true"
            if not include_inactive:
                qs = qs.filter(left_at__isnull=True)
        return qs

    def perform_create(self, serializer):
        team = self.get_team()
        if team is None or not team.is_managed_by(self.request.user):
            raise PermissionDenied(_("Only owner and managers can add members to a team."))

        member = serializer.validated_data["member"]
        if TeamMembership.objects.filter(team=team, member=member, left_at__isnull=True).exists():
            raise drf_serializers.ValidationError(
                {"member": _("This member is already in the team.")},
                code="already_member",
            )
        serializer.save(team=team)

    def perform_destroy(self, instance):
        user = self.request.user
        team = instance.team
        is_self = instance.member.user_id == user.pk
        is_team_manager = team.is_managed_by(user)

        if not (is_self or is_team_manager):
            raise PermissionDenied(_("You can only remove yourself or you must be a team manager."))
        if is_self and team.owner_id == user.pk:
            raise PermissionDenied(
                _(
                    "Team owner cannot leave their own team. "
                    "Transfer ownership first or delete the team."
                )
            )
        if instance.left_at is None:
            instance.left_at = timezone.now()
            instance.save(update_fields=["left_at", "updated_at"])
