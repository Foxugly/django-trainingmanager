import json
import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from wkhtmltopdf.views import PDFTemplateResponse

from event.forms import EventForm
from event.models import Event
from member.models import Member
from tools.crud_views import FullPageCreateView, FullPageDeleteView, FullPageUpdateView
from tools.generic_views import *


class EventCreateView(FullPageCreateView):
    model = Event
    form_class = EventForm
    success_url = reverse_lazy('index')
    success_message = _('event created.')


class EventListView(GenericListView):
    model = Event


class EventUpdateView(FullPageUpdateView):
    model = Event
    form_class = EventForm
    success_url = reverse_lazy('index')
    success_message = _('event updated.')


class EventDetailView(GenericDetailView):
    model = Event
    template_name = 'event.html'


class EventRawView(GenericDetailView):
    model = Event
    template_name = 'event_raw.html'


class EventDeleteView(FullPageDeleteView):
    model = Event
    success_url = reverse_lazy('index')
    success_message = _('event deleted.')


@login_required
def attendance_member(request, event_id, member_id):
    e = get_object_or_404(Event, id=event_id)
    m = get_object_or_404(Member, id=member_id)
    a = request.GET.get("attendance")
    if a == "true":
        if m not in e.members.all():
            e.members.add(m)
    else:
        if m in e.members.all():
            e.members.remove(m)
    results = {'nb_present': e.get_nb_members_present(), 'nb_members': e.get_nb_all_members(), 'return': True}
    return HttpResponse(json.dumps(results))


class PDFEventView(DetailView):
    model = Event
    template_name = 'event_raw.html'
    filename = 'event.pdf'

    def get(self, request, pk):
        # Build the context LOCALLY (not a shared class attribute — that dict was
        # mutated per request and could serve the wrong event PDF under concurrency).
        # wkhtmltopdf (enable-local-file-access) can't fetch a relative /static URL,
        # so the logo is an absolute file:// path built from STATIC_ROOT.
        context = {
            'title': 'Training Manager',
            'object': self.get_object(),
            'pdf': True,
            'logo_uri': 'file://' + os.path.join(settings.STATIC_ROOT, 'img', 'rbp.jpeg'),
        }
        return PDFTemplateResponse(request=request,
                                   template=self.template_name,
                                   filename=self.filename,
                                   context=context,
                                   show_content_in_browser=True,
                                   cmd_options={'margin-top': 50, 'enable-local-file-access': True},
                                   )
