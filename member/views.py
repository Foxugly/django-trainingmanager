from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _

from event.models import Event
from member.forms import MemberForm
from member.models import Member
from tools.crud_views import FullPageCreateView, FullPageDeleteView, FullPageUpdateView
from tools.generic_views import *


class MemberCreateView(FullPageCreateView):
    model = Member
    form_class = MemberForm
    success_url = reverse_lazy('index')
    success_message = _('member created.')

    def form_valid(self, form):
        response = super().form_valid(form)
        # When a member is created from an event page, enrol them in that event's
        # agenda so they show up in the attendance list.
        event_id = self.request.GET.get("event_id")
        if event_id:
            e = get_object_or_404(Event, id=event_id)
            e.refer_agenda.members.add(self.object)
        return response


class MemberListView(GenericListView):
    model = Member


class MemberUpdateView(FullPageUpdateView):
    model = Member
    form_class = MemberForm
    success_url = reverse_lazy('index')
    success_message = _('member updated.')


class MemberDetailView(GenericDetailView):
    model = Member


class MemberDeleteView(FullPageDeleteView):
    model = Member
    success_url = reverse_lazy('index')
    success_message = _('member deleted.')
