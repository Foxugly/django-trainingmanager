import json

from bootstrap_modal_forms.generic import BSModalCreateView, BSModalUpdateView, BSModalDeleteView
from django.http import HttpResponse
from django.utils.translation import gettext as _
from wkhtmltopdf.views import PDFTemplateResponse

from event.forms import BSEventForm
from event.models import Event
from member.models import Member
from tools.generic_views import *


class EventCreateView(BSModalCreateView):
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


class EventUpdateView(BSModalUpdateView):
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


class EventDeleteView(BSModalDeleteView):
    model = Event

    def get_success_url(self):
        if "next" in self.request.GET:
            return self.request.GET["next"]
        else:
            return self.success_url


def attendance_member(request, event_id, member_id):
    e = Event.objects.get(id=event_id)
    m = Member.objects.get(id=member_id)
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
    context = {'title': 'Hello World!'}

    def get(self, request, pk):
        self.context['object'] = self.get_object()
        response = PDFTemplateResponse(request=request,
                                       template=self.template_name,
                                       filename=self.filename,
                                       context=self.context,
                                       show_content_in_browser=True,
                                       cmd_options={'margin-top': 50, },
                                       )
        return response
