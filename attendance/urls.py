"""URL config for the attendance app.

Two namespaces:
- /api/v1/attendance-statuses/   (root referential, admin pattern)
- /api/v1/events/{event_pk}/attendance/   (nested under event)

The nested router uses a local parent registration to avoid colliding
with event/urls.py — same pattern as note/urls.py and chat/urls.py.
"""

from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from event.views import EventViewSet

from .views import AttendanceStatusViewSet, AttendanceViewSet

root_router = DefaultRouter()
root_router.register(r"attendance-statuses", AttendanceStatusViewSet, basename="attendance-status")

_parent = DefaultRouter()
_parent.register(r"events", EventViewSet, basename="attendance-parent-event")

attendance_router = NestedSimpleRouter(_parent, r"events", lookup="event")
attendance_router.register(r"attendance", AttendanceViewSet, basename="event-attendance")

urlpatterns = root_router.urls + attendance_router.urls
