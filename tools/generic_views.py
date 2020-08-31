from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView


class GenericCreateView(SuccessMessageMixin, CreateView):
    model = None
    app_name = None
    model_name = None
    fields = "__all__"
    template_name = 'update.html'
    success_url = reverse_lazy('%s:%s_list' % (app_name, model_name))
    success_message = _('object created.')

    def __init__(self, *args, **kwargs):
        if self.model:
            self.app_name = self.model._meta.app_label
            self.model_name = self.model._meta.model_name
            self.success_url = reverse_lazy('%s:%s_list' % (self.app_name, self.model_name))
        super(GenericCreateView, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(GenericCreateView, self).get_context_data(**kwargs)
        # context['model'] = self.model
        return context


class GenericListView(ListView):
    model = None
    paginate_by = 10
    ordering = ['pk']
    template_name = 'list.html'

    def __init__(self, *args, **kwargs):
        super(GenericListView, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(GenericListView, self).get_context_data(**kwargs)
        context['model'] = self.model
        return context


class GenericUpdateView(SuccessMessageMixin, UpdateView):
    model = None
    app_name = None
    model_name = None
    fields = '__all__'
    template_name = 'update.html'
    success_url = None
    success_message = _('object updated.')

    def __init__(self, *args, **kwargs):
        if self.model:
            self.app_name = self.model._meta.app_label
            self.model_name = self.model._meta.model_name
            self.success_url = reverse_lazy('%s:%s_list' % (self.app_name, self.model_name))
        super(GenericUpdateView, self).__init__(*args, **kwargs)

    def get_object(self):
        return self.model.objects.get(pk=self.kwargs['pk'])
        # return get_object_or_404(self.model, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super(GenericUpdateView, self).get_context_data(**kwargs)
        context['model'] = self.model
        return context


class GenericDetailView(DetailView):
    model = None
    app_name = None
    model_name = None
    template_name = 'detail.html'
    success_url = None

    def __init__(self, *args, **kwargs):
        if self.model:
            self.app_name = self.model._meta.app_label
            self.model_name = self.model._meta.model_name
            self.success_url = reverse_lazy('%s:%s_list' % (self.app_name, self.model_name))
        super(GenericDetailView, self).__init__(*args, **kwargs)

    def get_success_url(self):
        return self.success_url


class GenericDeleteView(SuccessMessageMixin, DeleteView):
    model = None
    app_name = None
    model_name = None
    success_message = _('object deleted.')

    def __init__(self, *args, **kwargs):
        if self.model:
            self.app_name = self.model._meta.app_label
            self.model_name = self.model._meta.model_name
            self.success_url = reverse_lazy('%s:%s_list' % (self.app_name, self.model_name))
        super(GenericDeleteView, self).__init__(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)

    def get_success_url(self):
        return self.success_url
