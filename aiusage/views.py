from django.db.models import Count, Sum
from django.db.models.functions import TruncDay, TruncMonth, TruncWeek, TruncYear
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from team.models import Team

from .models import AIUsage
from .serializers import AIUsageAggregateResponseSerializer, AIUsageDetailSerializer

PERIOD_TRUNC_MAP = {
    "day": TruncDay,
    "week": TruncWeek,
    "month": TruncMonth,
    "year": TruncYear,
}

PERIOD_FORMAT_MAP = {
    "day": "%Y-%m-%d",
    "week": "%Y-W%V",
    "month": "%Y-%m",
    "year": "%Y",
}


def _check_team_access(user, team):
    """Allow access only to the team's owner and managers."""
    is_authorized = team.owner_id == user.pk or team.managers.filter(pk=user.pk).exists()
    if not is_authorized:
        raise PermissionDenied(_("Only the owner and managers of this team can view AI usage."))


class TeamAIUsageViewSet(viewsets.GenericViewSet):
    """AI usage endpoints scoped to a specific team. Owner + managers only."""

    permission_classes = [IsAuthenticated]
    serializer_class = AIUsageDetailSerializer
    queryset = AIUsage.objects.all()

    @extend_schema(
        summary="AI usage aggregated by period for a team",
        parameters=[
            OpenApiParameter(
                name="period",
                type=OpenApiTypes.STR,
                required=False,
                description="One of: day, week, month, year (default: month).",
            ),
            OpenApiParameter(name="start", type=OpenApiTypes.DATE, required=False),
            OpenApiParameter(name="end", type=OpenApiTypes.DATE, required=False),
            OpenApiParameter(
                name="exclude_ping",
                type=OpenApiTypes.BOOL,
                required=False,
                description="Exclude /ai/ping/ from aggregates (default true).",
            ),
        ],
        responses={200: AIUsageAggregateResponseSerializer},
    )
    def by_team(self, request, team_id=None):
        """GET /api/v1/teams/ai-usage/{team_id}/?period=month"""
        team = get_object_or_404(Team, pk=team_id)
        _check_team_access(request.user, team)

        period = request.query_params.get("period", "month")
        if period not in PERIOD_TRUNC_MAP:
            return Response(
                {
                    "code": "invalid_period",
                    "detail": _("period must be one of: day, week, month, year."),
                },
                status=400,
            )

        exclude_ping = request.query_params.get("exclude_ping", "true").lower() == "true"

        qs = AIUsage.objects.filter(team=team)
        if exclude_ping:
            qs = qs.exclude(endpoint=AIUsage.Endpoint.PING)

        start = request.query_params.get("start")
        end = request.query_params.get("end")
        if start:
            qs = qs.filter(created_at__gte=start)
        if end:
            qs = qs.filter(created_at__lte=end)

        trunc = PERIOD_TRUNC_MAP[period]
        agg = (
            qs.annotate(period_bucket=trunc("created_at"))
            .values("period_bucket")
            .annotate(
                total_calls=Count("id"),
                total_tokens=Sum("total_tokens"),
                input_tokens=Sum("input_tokens"),
                output_tokens=Sum("output_tokens"),
            )
            .order_by("period_bucket")
        )

        fmt = PERIOD_FORMAT_MAP[period]
        results = [
            {
                "period": row["period_bucket"].strftime(fmt) if row["period_bucket"] else None,
                "total_calls": row["total_calls"],
                "total_tokens": row["total_tokens"] or 0,
                "input_tokens": row["input_tokens"] or 0,
                "output_tokens": row["output_tokens"] or 0,
            }
            for row in agg
        ]

        return Response(
            {
                "team_id": team.pk,
                "period": period,
                "exclude_ping": exclude_ping,
                "data": results,
            }
        )

    @extend_schema(
        summary="AI usage detailed rows for a team",
        parameters=[
            OpenApiParameter(name="since", type=OpenApiTypes.DATETIME, required=False),
            OpenApiParameter(name="endpoint", type=OpenApiTypes.STR, required=False),
        ],
        responses={200: AIUsageDetailSerializer(many=True)},
    )
    def by_team_details(self, request, team_id=None):
        """GET /api/v1/teams/ai-usage/{team_id}/details/?since=2026-04-01"""
        team = get_object_or_404(Team, pk=team_id)
        _check_team_access(request.user, team)

        qs = AIUsage.objects.filter(team=team).select_related("user")

        since = request.query_params.get("since")
        endpoint = request.query_params.get("endpoint")
        if since:
            qs = qs.filter(created_at__gte=since)
        if endpoint:
            qs = qs.filter(endpoint=endpoint)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = AIUsageDetailSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(AIUsageDetailSerializer(qs, many=True).data)
