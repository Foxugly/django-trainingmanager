import json
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _

from agenda.forms import AgendaForm
from agenda.models import Agenda
from event.models import Event
from tools.crud_views import FullPageCreateView, FullPageDeleteView, FullPageUpdateView
from tools.generic_views import *


class AgendaCreateView(FullPageCreateView):
    model = Agenda
    form_class = AgendaForm
    success_url = reverse_lazy('agenda:agenda_list')
    success_message = _('agenda created.')


class AgendaListView(GenericListView):
    model = Agenda


class AgendaUpdateView(FullPageUpdateView):
    model = Agenda
    form_class = AgendaForm
    success_url = reverse_lazy('agenda:agenda_list')
    success_message = _('agenda updated.')


class AgendaDetailView(GenericDetailView):
    model = Agenda
    template_name = 'agenda.html'


class AgendaDeleteView(FullPageDeleteView):
    model = Agenda
    success_url = reverse_lazy('agenda:agenda_list')
    success_message = _('agenda deleted.')


def qdict_to_dict(qdict):
    return {k: v[0] if len(v) == 1 else v for k, v in qdict.lists()}


@login_required
def create_events(request, agenda_id):
    results = {}
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == "GET":
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
            a = get_object_or_404(Agenda, id=agenda_id)
            e.refer_agenda = a
            e.save()
            a.events.add(e)
            results['events'] = [e.as_json() for e in a.get_events()]
        elif date_start <= date_end:
            a = get_object_or_404(Agenda, id=agenda_id)
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


@login_required
def get_events_json(request, agenda_id):
    a = get_object_or_404(Agenda, id=agenda_id)
    return HttpResponse(json.dumps([e.as_json() for e in a.get_events()]))
