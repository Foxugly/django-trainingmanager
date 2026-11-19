from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.forms import ModelForm
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import UpdateView

from customuser.models import CustomUser


class CustomUserForm(ModelForm):
    # Self-service profile form: only harmless fields. is_superuser and
    # is_foo_admin used to be listed here with an HTML-only "disabled" attribute,
    # so a crafted POST could grant them. Privileges are edited in the admin.
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'language']


class CustomUserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserForm
    template_name = 'update.html'
    success_url = reverse_lazy('update_user')
    success_message = _('Changes saved.')

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['model'] = self.model
        return context
