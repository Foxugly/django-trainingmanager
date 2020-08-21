from django.shortcuts import render
from django.views.generic import UpdateView
from customuser.models import CustomUser
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.forms import ModelForm
from django.contrib.messages.views import SuccessMessageMixin


class CustomUserForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(CustomUserForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.fields['is_foo_admin'].widget.attrs['readonly'] = True
            self.fields['is_foo_admin'].widget.attrs['disabled'] = 'disabled'
            self.fields['is_superuser'].widget.attrs['readonly'] = True
            self.fields['is_superuser'].widget.attrs['disabled'] = 'disabled'

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'language', 'is_foo_admin', 'is_superuser', ]


class CustomUserUpdateView(SuccessMessageMixin, UpdateView):
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
