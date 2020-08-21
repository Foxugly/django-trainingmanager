from tools.generic_urls import add_url_from_generic_views
from agenda.views import create_events, get_events_json
from django.urls import path


app_name = 'agenda'
urlpatterns = add_url_from_generic_views('agenda.views')
urlpatterns.append(path('<int:agenda_id>/events/add/', create_events, name="create_events"))
urlpatterns.append(path('<int:agenda_id>/events/json/', get_events_json, name="events_json"))