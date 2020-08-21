class BuildClass:
    app_label = None
    class_label = None
    class_name = None
    txt = ""

    def __init__(self, app_label, class_label, class_name):
        self.app_label = app_label
        self.class_label = class_label
        self.class_name = class_name

    def createview(self):
        self.txt += "class %sCreateView(SuccessMessageMixin, CreateBreadcrumbMixin, CreateView):\n" % self.class_name
        self.txt += "    model = %s\n" % self.class_name
        self.txt += "    fields = '__all__'\n"
        self.txt += "    template_name = 'update.html'\n"
        self.txt += "    success_url = reverse_lazy('%s:%s_list')\n" % (self.app_label, self.class_label)
        self.txt += "    success_message = _('object created.')\n\n"
        self.txt += "    def get_context_data(self, **kwargs):\n"
        self.txt += "        context = super(%sCreateView, self).get_context_data(**kwargs)\n" % self.class_name
        self.txt += "        return context\n\n\n"

    def listview(self):
        self.txt += "class %sListView(ListBreadcrumbMixin, ListView):\n" % self.class_name
        self.txt += "    model = %s\n" % self.class_name
        self.txt += "    paginate_by = 10\n"
        self.txt += "    ordering = ['pk']\n"
        self.txt += "    template_name = 'list.html'\n\n"
        self.txt += "    def get_context_data(self, **kwargs):\n"
        self.txt += "        context = super(%sListView, self).get_context_data(**kwargs)\n" % self.class_name
        self.txt += "        context['model'] = self.model\n"
        self.txt += "        return context\n\n\n"

    def updateview(self):
        self.txt += "class %sUpdateView(SuccessMessageMixin, UpdateBreadcrumbMixin, UpdateView):\n" % self.class_name
        self.txt += "    model = %s\n" % self.class_name
        self.txt += "    fields = '__all__'\n"
        self.txt += "    template_name = 'update.html'\n"
        self.txt += "    success_url = reverse_lazy('%s:%s_list')\n" % (self.app_label, self.class_label)
        self.txt += "    success_message = _('object updated.')\n\n"
        self.txt += "    def get_object(self):\n"
        self.txt += "        return %s.objects.get(pk=self.kwargs['pk'])\n\n" % self.class_name
        self.txt += "    def get_context_data(self, **kwargs):\n"
        self.txt += "        context = super(%sUpdateView, self).get_context_data(**kwargs)\n" % self.class_name
        self.txt += "        context['model'] = self.model\n"
        self.txt += "        return context\n\n\n"

    def detailview(self):
        self.txt += "class %sDetailView(DetailBreadcrumbMixin, DetailView):\n" % self.class_name
        self.txt += "    model = %s\n" % self.class_name
        self.txt += "    template_name = 'detail.html'\n\n\n"

    def deleteview(self):
        self.txt += "class %sDeleteView(SuccessMessageMixin, DeleteView):\n" % self.class_name
        self.txt += "    model = %s\n" % self.class_name
        self.txt += "    success_message = _('object deleted.')\n\n"
        self.txt += "    def get(self, *args, **kwargs):\n"
        self.txt += "        return self.post(*args, **kwargs)\n\n"
        self.txt += "    def get_success_url(self):\n"
        self.txt += "        return reverse_lazy('%s:%s_list')\n\n\n" % (self.app_label, self.class_label)

    def headerview(self):
        self.txt += "from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView\n"
        self.txt += "from view_breadcrumbs import ListBreadcrumbMixin, UpdateBreadcrumbMixin, DetailBreadcrumbMixin, CreateBreadcrumbMixin\n"
        self.txt += "from django.contrib.messages.views import SuccessMessageMixin\n"
        self.txt += "from django.utils.translation import gettext as _\n"
        self.txt += "from django.urls import reverse_lazy\n"
        self.txt += "from %s.models import %s\n\n\n" % (self.app_label, self.class_name)

    def urls(self):
        self.txt += "from django.urls import path\n"
        self.txt += "from %s.views import %sListView, %sUpdateView, %sDetailView, %sCreateView, %sDeleteView\n\n" % (
            self.app_label, self.class_name, self.class_name, self.class_name, self.class_name, self.class_name)
        self.txt += "app_name = '%s'\n" % self.app_label
        self.txt += "urlpatterns = [\n"
        self.txt += "    path('%s/', %sListView.as_view(), name='%s_list'),\n" % (
            self.class_label, self.class_name, self.class_label)
        self.txt += "    path('%s/add/', %sCreateView.as_view(), name='%s_add'),\n" % (
            self.class_label, self.class_name, self.class_label)
        self.txt += "    path('%s/<int:pk>/change/', %sUpdateView.as_view(), name='%s_change'),\n" % (
            self.class_label, self.class_name, self.class_label)
        self.txt += "    path('%s/<int:pk>/', %sDetailView.as_view(), name='%s_detail'),\n" % (
            self.class_label, self.class_name, self.class_label)
        self.txt += "    path('%s/<int:pk>/delete', %sDeleteView.as_view(), name='%s_delete'),\n" % (
            self.class_label, self.class_name, self.class_label)
        self.txt += "]\n"

    def models(self):
        self.txt += "from django.db import models\n"
        self.txt += "from django.urls import reverse\n"
        self.txt += "from django.utils.translation import gettext as _\n\n\n"
        self.txt += "class %s(models.Model):\n" % self.class_name
        self.txt += "    name = models.CharField(max_length=100, verbose_name=_('name'))\n"
        self.txt += "    # add fields here\n\n"
        self.txt += "    def get_absolute_url(self):\n"
        self.txt += "        return reverse('%s:%s_change', kwargs={'pk': self.pk})\n\n" % (
            self.app_label, self.class_label)
        self.txt += "    def get_add_url(self):\n"
        self.txt += "        return reverse('%s:%s_add')\n\n" % (self.app_label, self.class_label)
        self.txt += "    def get_detail_url(self):\n"
        self.txt += "        return reverse('%s:%s_detail', kwargs={'pk': self.pk})\n\n" % (
            self.app_label, self.class_label)
        self.txt += "    def get_delete_url(self):\n"
        self.txt += "        return reverse('%s:%s_delete', kwargs={'pk': self.pk})\n\n" % (
            self.app_label, self.class_label)
        self.txt += "    def get_list_url(self):\n"
        self.txt += "        return reverse('%s:%s_list')\n\n" % (self.app_label, self.class_label)
        self.txt += "    def __str__(self):\n"
        self.txt += "        return self.name\n\n"
        self.txt += "    class Meta:\n"
        self.txt += "        verbose_name = _('%s')\n" % self.class_name

    def run(self):
        self.txt += "# ================== VIEWS ================ \n\n"
        self.headerview()
        self.createview()
        self.listview()
        self.updateview()
        self.detailview()
        self.deleteview()
        self.txt += "# ================== URLS ================ \n\n"
        self.urls()
        self.txt += "# ================== MODELS ================ \n\n"
        self.models()
        print(self.txt)


if __name__ == '__main__':
    b = BuildClass("myapp", "myclass", "MyClass")
    b.run()
