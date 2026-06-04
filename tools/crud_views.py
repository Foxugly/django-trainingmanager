from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import CreateView, DeleteView, UpdateView


class NextUrlMixin:
    """Honour a ?next= query param for the post-save redirect.

    The full-page CRUD forms post back to the same URL (``action=""``), so the
    original querystring — including ``next`` — survives the POST. This replaces
    the old modal flow where the JS plugin threaded ``next`` through AJAX.
    """

    def get_success_url(self):
        return self.request.GET.get("next") or str(self.success_url)


class ModelContextMixin:
    """Expose the model class to the template (drives the page heading)."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("model", self.model)
        return context


class FullPageCreateView(LoginRequiredMixin, SuccessMessageMixin, NextUrlMixin, ModelContextMixin, CreateView):
    template_name = "update.html"


class FullPageUpdateView(LoginRequiredMixin, SuccessMessageMixin, NextUrlMixin, ModelContextMixin, UpdateView):
    template_name = "update.html"


class FullPageDeleteView(LoginRequiredMixin, SuccessMessageMixin, NextUrlMixin, ModelContextMixin, DeleteView):
    template_name = "delete.html"
