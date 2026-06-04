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
        if "next" in self.request.GET:
            return self.request.GET["next"]
        else:
            return self.success_url


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
        if "next" in self.request.GET:
            return self.request.GET["next"]
        else:
            return self.success_url


class EventDetailView(GenericDetailView):
    model = Event
    template_name = 'event.html'


class EventRawView(GenericDetailView):
    model = Event
    template_name = 'event_raw.html'


class EventDeleteView(LoginRequiredMixin, BSModalDeleteView):
    model = Event

    def get_success_url(self):
        if "next" in self.request.GET:
            return self.request.GET["next"]
        else:
            return self.success_url


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
