from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets

from team.models import Team

from .models import Message
from .permissions import IsTeamMemberAndChatPolicy
from .serializers import MessageListQuerySerializer, MessageSerializer

SINCE_PARAM = OpenApiParameter(
    name="since",
    type=OpenApiTypes.DATETIME,
    location=OpenApiParameter.QUERY,
    required=False,
    description=(
        "Returns messages created strictly AFTER this timestamp. "
        "Used for polling: pass the timestamp of the most recent message "
        "you have."
    ),
)

BEFORE_PARAM = OpenApiParameter(
    name="before",
    type=OpenApiTypes.DATETIME,
    location=OpenApiParameter.QUERY,
    required=False,
    description=(
        "Returns messages created strictly BEFORE this timestamp. "
        "Used for historical scroll: pass the timestamp of the oldest "
        "message you have."
    ),
)

LIMIT_PARAM = OpenApiParameter(
    name="limit",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Maximum number of messages to return. Default 50, max 200.",
)


@extend_schema_view(
    list=extend_schema(
        parameters=[SINCE_PARAM, BEFORE_PARAM, LIMIT_PARAM],
        summary="List team chat messages with cursor-based pagination",
        description=(
            "Three modes:\n"
            "- Initial load: ?limit=50 returns the 50 most recent messages "
            "(default order: newest first).\n"
            "- Polling: ?since=<ISO timestamp> returns messages created "
            "strictly after the given timestamp (chronological order).\n"
            "- Historical scroll: ?before=<ISO timestamp>&limit=50 returns "
            "50 messages older than the given timestamp.\n"
            "\n"
            "Soft-deleted messages are returned with deleted_at set so the "
            "frontend can render a 'message deleted' placeholder."
        ),
    ),
)
class MessageViewSet(viewsets.ModelViewSet):
    """CRUD on team chat messages with cursor-based pagination.

    URL: /api/v1/teams/{team_pk}/messages/
    """

    serializer_class = MessageSerializer
    permission_classes = [IsTeamMemberAndChatPolicy]
    pagination_class = None

    DEFAULT_LIMIT = 50
    MAX_LIMIT = 200

    def get_team(self):
        team_pk = self.kwargs.get("team_pk")
        if not team_pk:
            return None
        return get_object_or_404(Team, pk=team_pk)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Message.objects.none()

        team = self.get_team()
        if team is None:
            return Message.objects.none()

        qs = Message.objects.filter(team=team).select_related("author")

        # retrieve / update / destroy use the unsliced queryset so DRF
        # can resolve {pk} via .filter(pk=...).get(). Cursor params and
        # slicing apply only on list.
        if self.action != "list":
            return qs

        # I5: validate ?since/?before/?limit via a dedicated serializer so
        # malformed input returns a consistent 400 instead of a 500 from
        # the ORM (?since=foo) or a silent fallback (?limit=abc → 50).
        query_serializer = MessageListQuerySerializer(data=self.request.query_params)
        query_serializer.is_valid(raise_exception=True)
        qp = query_serializer.validated_data

        since = qp.get("since")
        before = qp.get("before")
        limit = qp.get("limit", self.DEFAULT_LIMIT)

        if since:
            qs = qs.filter(created_at__gt=since).order_by("created_at")
        elif before:
            qs = qs.filter(created_at__lt=before).order_by("-created_at")
        else:
            qs = qs.order_by("-created_at")

        return qs[:limit]

    def perform_create(self, serializer):
        team = self.get_team()
        serializer.save(team=team, author=self.request.user)

    def perform_update(self, serializer):
        # Set edited_at the first time a message is updated, in the same
        # SQL UPDATE as the user-facing change (instead of save() + a
        # second save(update_fields=["edited_at"])).
        kwargs = {}
        if not serializer.instance.edited_at:
            kwargs["edited_at"] = timezone.now()
        serializer.save(**kwargs)

    def perform_destroy(self, instance):
        if not instance.deleted_at:
            instance.deleted_at = timezone.now()
            instance.save(update_fields=["deleted_at"])
