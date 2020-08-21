import json
from datetime import datetime, timedelta

from bootstrap_modal_forms.generic import BSModalCreateView, BSModalUpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from agenda.forms import AgendaForm, BSAgendaCreateForm
from agenda.models import Agenda
from event.models import Event
from tools.generic_views import *


class AgendaCreateView(BSModalCreateView):
    model = Agenda
    fields = None
    form_class = BSAgendaCreateForm
    template_name = 'modal.html'
    success_url = reverse_lazy('agenda:agenda_list')
    success_message = _('agenda created.')

    def get_success_url(self):
        if "next" in self.request.GET:
            return self.request.GET["next"]
        else:
            return self.success_url


class AgendaListView(LoginRequiredMixin, GenericListView):
    model = Agenda


class AgendaUpdateView(BSModalUpdateView):
    model = Agenda
    fields = None
    form_class = BSAgendaCreateForm
    template_name = 'modal.html'
    success_url = reverse_lazy('agenda:agenda_list')
    success_message = _('agenda created.')

    def get_success_url(self):
        if "next" in self.request.GET:
            return self.request.GET["next"]
        else:
            return self.success_url


class AgendaDetailView(LoginRequiredMixin, GenericDetailView):
    model = Agenda
    template_name = 'agenda.html'


class AgendaDeleteView(LoginRequiredMixin, GenericDeleteView):
    model = Agenda

    def get_success_url(self):
        if "next" in self.request.GET:
            return self.request.GET["next"]
        else:
            return self.success_url


def qdict_to_dict(qdict):
    return {k: v[0] if len(v) == 1 else v for k, v in qdict.lists()}


def create_events(request, agenda_id):
    results = {}
    if request.is_ajax() and request.method == "GET":
        dict_get = qdict_to_dict(request.GET)
        name = dict_get['name']
        color = dict_get['color']
        date_start = datetime.strptime(dict_get['date_start'], '%Y-%m-%d')
        date_end = datetime.strptime(dict_get['date_end'], '%Y-%m-%d')
        hour_start = dict_get['hour_start']
        hour_end = dict_get['hour_end']
        if 'days' in request.GET:
            days = dict_get['days']
        results['return'] = True
        if date_start == date_end:
            e = Event(name=name, date=date_start, hour_start=hour_start, hour_end=hour_end)
            e.save()
            a = Agenda.objects.get(id=agenda_id)
            a.trainings.add(e)
            results['events'] = [e.as_json() for e in a.get_events()]
        elif date_start <= date_end:
            a = Agenda.objects.get(id=agenda_id)
            delta = timedelta(days=1)
            while date_start <= date_end:
                if str(date_start.weekday()) in list(days):
                    e = Event(name=name, date=date_start, hour_start=hour_start, hour_end=hour_end, color=color,
                              refer_agenda=a)
                    e.save()
                    a.events.add(e)
                date_start += delta
        else:
            results['return'] = False
    return HttpResponse(json.dumps(results))


def get_events_json(request, agenda_id):
    a = Agenda.objects.get(id=agenda_id)
    return HttpResponse(json.dumps([e.as_json() for e in a.get_events()]))
