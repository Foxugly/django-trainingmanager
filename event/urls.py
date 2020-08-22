from django.urls import path
from event.views import PDFEventView, EventRawView, member_attendance
from tools.generic_urls import add_url_from_generic_views

app_name = 'event'
urlpatterns = add_url_from_generic_views('event.views')
urlpatterns.append(path('event/<int:pk>/raw/', EventRawView.as_view(), name="event_raw"))
urlpatterns.append(path('event/<int:pk>/pdf/', PDFEventView.as_view(), name="event_pdf"))
urlpatterns.append(path('event/<int:pk>/member/<int:member_id>/attendance/', member_attendance, name="member_attendance"))
