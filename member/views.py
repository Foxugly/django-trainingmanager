from tools.generic_views import *
from member.models import Member
from member.forms import BSMemberForm
from django.utils.translation import gettext as _
from bootstrap_modal_forms.generic import BSModalCreateView, BSModalUpdateView, BSModalDeleteView


class MemberCreateView(BSModalCreateView):
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


class MemberListView(GenericListView):
    model = Member


class MemberUpdateView(BSModalUpdateView):
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


class MemberDeleteView(BSModalDeleteView):
    model = Member

    def get_success_url(self):
        if "next" in self.request.GET:
            return self.request.GET["next"]
        else:
            return self.success_url
