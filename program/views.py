from datetime import date as _date

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from team.queries import managed_teams, user_visible_teams
from tools.openapi import INCLUDE_INACTIVE_PARAM
from tools.throttling import AIPlanGenerationThrottle

from .ai import generate_plan
from .models import Program
from .serializers import GeneratePlanRequestSerializer, ProgramSerializer


@extend_schema_view(
    list=extend_schema(parameters=[INCLUDE_INACTIVE_PARAM]),
    retrieve=extend_schema(parameters=[INCLUDE_INACTIVE_PARAM]),
    update=extend_schema(parameters=[INCLUDE_INACTIVE_PARAM]),
    partial_update=extend_schema(parameters=[INCLUDE_INACTIVE_PARAM]),
    destroy=extend_schema(
        summary="Soft delete program (manager of team only)",
        description="Sets is_active=False; does not hard delete.",
    ),
)
class ProgramViewSet(viewsets.ModelViewSet):
    """CRUD complet pour Program, scopé par team.

    Soft-delete convention: DELETE flips is_active=False (no hard delete).
    Default queryset hides is_active=False. ?include_inactive=true is honored
    for staff (sees all inactives across visible teams) and for managers
    (sees inactives of teams they manage).
    """

    serializer_class = ProgramSerializer
    filterset_fields = ["name", "date_start", "date_end", "team", "is_active"]
    search_fields = ["name"]
    ordering_fields = ["name", "date_start", "date_end"]
    ordering = ["name"]

    def get_queryset(self):
        user = self.request.user
        base = (
            Program.objects.filter(team__in=user_visible_teams(user))
            .select_related("team", "team__sport", "team__owner")
            .prefetch_related("events")
        )
        include_inactive = self.request.query_params.get("include_inactive") == "true"
        if include_inactive and user.is_authenticated and user.is_staff:
            return base
        if include_inactive and user.is_authenticated:
            return base.filter(Q(is_active=True) | Q(team__in=managed_teams(user)))
        return base.filter(is_active=True)

    def _check_team_write(self, team):
        if team is None or not managed_teams(self.request.user).filter(pk=team.pk).exists():
            raise PermissionDenied(_("You do not manage this team."))

    def perform_create(self, serializer):
        self._check_team_write(serializer.validated_data.get("team"))
        serializer.save()

    def perform_update(self, serializer):
        self._check_team_write(serializer.validated_data.get("team", serializer.instance.team))
        serializer.save()

    def perform_destroy(self, instance):
        self._check_team_write(instance.team)
        instance.is_active = False
        instance.save(update_fields=["is_active"])

    @extend_schema(
        request=GeneratePlanRequestSerializer,
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name="GeneratePlanResponse",
                    fields={
                        "created_count": serializers.IntegerField(),
                        "deleted_count": serializers.IntegerField(),
                        "rationale": serializers.CharField(),
                        "model": serializers.CharField(),
                        "tokens_used": inline_serializer(
                            name="GeneratePlanTokensUsed",
                            fields={
                                "input": serializers.IntegerField(),
                                "output": serializers.IntegerField(),
                            },
                        ),
                    },
                ),
                description="Plan generated successfully",
            ),
            400: OpenApiResponse(description="Invalid request data"),
            403: OpenApiResponse(description="Not a manager of this program team"),
            500: OpenApiResponse(description="AI configuration error"),
            502: OpenApiResponse(description="AI service error"),
        },
        description="Generate a training plan with AI for the given Program.",
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="generate-events",
        throttle_classes=[AIPlanGenerationThrottle],
    )
    def generate_events(self, request, pk=None):
        """POST /programs/{id}/generate-events/ — Claude-generated session list."""
        program = self.get_object()

        if not program.team.is_managed_by(request.user):
            return Response(
                {
                    "code": "not_a_manager",
                    "detail": _("You must be owner or manager of this program's team."),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = GeneratePlanRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        ai_result = generate_plan(
            program=program,
            date_start=data["date_start"],
            date_end=data["date_end"],
            frequency_per_week=data["frequency_per_week"],
            description=data["description"],
            user=request.user if request.user.is_authenticated else None,
        )

        with transaction.atomic():
            created_count, deleted_count = self._apply_overlap_strategy(
                program=program,
                new_events_data=ai_result["events"],
                strategy=data["overlap_strategy"],
                date_start=data["date_start"],
                date_end=data["date_end"],
            )

            program.frequency_per_week = data["frequency_per_week"]
            program.description = data["description"]
            program.generated_by_ai = True
            program.ai_prompt = ai_result["prompt_sent"]
            program.ai_response = ai_result["rationale"]
            program.ai_generated_at = timezone.now()
            program.save()

        return Response(
            {
                "created_count": created_count,
                "deleted_count": deleted_count,
                "rationale": ai_result["rationale"],
                "model": ai_result["model"],
                "tokens_used": {
                    "input": ai_result["input_tokens"],
                    "output": ai_result["output_tokens"],
                },
            },
            status=status.HTTP_200_OK,
        )

    def _apply_overlap_strategy(self, *, program, new_events_data, strategy, date_start, date_end):
        from event.models import Event

        deleted_count = 0
        if strategy == "replace":
            existing = Event.objects.filter(
                refer_program=program,
                date__gte=date_start,
                date__lte=date_end,
            )
            deleted_count = existing.count()
            existing.delete()

        created_count = 0
        for ev_data in new_events_data:
            ev_date = _date.fromisoformat(ev_data["date"])

            if strategy == "add_only":
                if Event.objects.filter(refer_program=program, date=ev_date).exists():
                    continue

            Event.objects.create(
                refer_program=program,
                name=ev_data["name"][:100],
                goal=ev_data["goal"][:100],
                date=ev_date,
                color=ev_data["color"],
                total=ev_data["total_distance"],
            )
            created_count += 1

        return created_count, deleted_count
