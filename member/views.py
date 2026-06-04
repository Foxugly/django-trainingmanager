from bootstrap_modal_forms.generic import BSModalCreateView, BSModalUpdateView, BSModalDeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _

from event.models import Event
from member.forms import BSMemberForm
from member.models import Member
from tools.generic_views import *


class MemberCreateView(LoginRequiredMixin, BSModalCreateView):
    model = Member
    fields = None
    form_class = BSMemberForm
    template_name = 'modal.html'
    success_url = reverse_lazy('index')
    success_message = _('event created.')

    def get_success_url(self):
        if "next" in self.request.GET:
            return self.request.GET["next"]
        else:
            return self.success_url

    def form_valid(self, form):
        if self.request.headers.get('x-requested-with') != 'XMLHttpRequest':
            if "event_id" in self.request.GET:
                f = form.save(commit=False)
                f.save()
                e = get_object_or_404(Event, id=self.request.GET['event_id'])
                e.refer_agenda.members.add(f)
        return super(MemberCreateView, self).form_valid(form)


class MemberListView(GenericListView):
    model = Member


class MemberUpdateView(LoginRequiredMixin, BSModalUpdateView):
    model = Member
    fields = None
    form_class = BSMemberForm
    template_name = 'modal.html'
    success_url = reverse_lazy('index')
    success_message = _('event created.')

    def get_success_url(self):
        if "next" in self.request.GET:
            return self.request.GET["next"]
        else:
            return self.success_url


class MemberDetailView(GenericDetailView):
    model = Member


class MemberDeleteView(LoginRequiredMixin, BSModalDeleteView):
    model = Member

    def get_success_url(self):
        if "next" in self.request.GET:
            return self.request.GET["next"]
        else:
            return self.success_url
