from django.urls import path

from .views import TeamAIUsageViewSet

# /api/v1/teams/<team_id>/ai-usage/         GET  -> aggregated by period
# /api/v1/teams/<team_id>/ai-usage/details/ GET  -> raw rows (paginated)
urlpatterns = [
    path(
        "teams/<int:team_id>/ai-usage/",
        TeamAIUsageViewSet.as_view({"get": "by_team"}),
        name="team-ai-usage",
    ),
    path(
        "teams/<int:team_id>/ai-usage/details/",
        TeamAIUsageViewSet.as_view({"get": "by_team_details"}),
        name="team-ai-usage-details",
    ),
]
