import base64
import json
import os

from bootstrap_modal_forms.generic import BSModalCreateView, BSModalUpdateView, BSModalDeleteView
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from wkhtmltopdf.views import PDFTemplateResponse

from event.forms import BSEventForm
from event.models import Event
from member.models import Member
from tools.generic_views import *


class EventCreateView(LoginRequiredMixin, BSModalCreateView):
    model = Event
    fields = None
    form_class = BSEventForm
    template_name = 'modal.html'
    success_url = reverse_lazy('index')
    success_message = _('event created.')

    def get_success_url(self):
        return safe_next_url(self.request, self.success_url)


class EventListView(GenericListView):
    model = Event


class EventUpdateView(LoginRequiredMixin, BSModalUpdateView):
    model = Event
    fields = None
    form_class = BSEventForm
    template_name = 'modal.html'
    success_url = reverse_lazy('index')
    success_message = _('event created.')

    def get_success_url(self):
        return safe_next_url(self.request, self.success_url)


class EventDetailView(GenericDetailView):
    model = Event
    template_name = 'event.html'


class EventRawView(GenericDetailView):
    model = Event
    template_name = 'event_raw.html'


class EventDeleteView(LoginRequiredMixin, BSModalDeleteView):
    model = Event

    def get_success_url(self):
        return safe_next_url(self.request, self.success_url)


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


# wkhtmltopdf options for the event export. The HTML is ours, but it carries
# user-entered text: no JavaScript, and no access to local files (an injected
# <iframe src="file:///run/<app>/.env"> used to land in the PDF). The logo is
# inlined as a data: URI, so nothing has to be read from disk by wkhtmltopdf.
PDF_CMD_OPTIONS = {
    'margin-top': 50,
    'disable-javascript': True,
    'disable-local-file-access': True,
}


def _logo_data_uri():
    path = os.path.join(settings.STATIC_ROOT, 'img', 'rbp.jpeg')
    try:
        with open(path, 'rb') as fh:
            return 'data:image/jpeg;base64,' + base64.b64encode(fh.read()).decode('ascii')
    except OSError:
        return ''


class PDFEventView(GenericDetailView):
    # Same access rule as EventDetailView (login required). It used to be a bare
    # DetailView: anyone could enumerate /event/event/<id>/pdf/ and spawn a
    # wkhtmltopdf process per request.
    model = Event
    template_name = 'event_raw.html'
    filename = 'event.pdf'

    def get(self, request, *args, **kwargs):
        # Build the context LOCALLY (not a shared class attribute — that dict was
        # mutated per request and could serve the wrong event PDF under concurrency).
        context = {
            'title': 'Training Manager',
            'object': self.get_object(),
            'pdf': True,
            'logo_uri': _logo_data_uri(),
        }
        return PDFTemplateResponse(request=request,
                                   template=self.template_name,
                                   filename=self.filename,
                                   context=context,
                                   show_content_in_browser=True,
                                   cmd_options=PDF_CMD_OPTIONS,
                                   )
