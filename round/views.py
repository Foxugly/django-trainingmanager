from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _

from event.models import Event
from round.forms import RoundForm, RoundExerciseFormSet
from round.models import Round
from tools.crud_views import FullPageCreateView, FullPageDeleteView, FullPageUpdateView
from tools.generic_views import *


def _add_exercise_formset(view, context):
    """Attach the inline exercise formset + button labels to a round-form context."""
    context['add_exercise'] = _("Ajouter un exercice")
    context['delete_exercise'] = _("supprimer")
    context['exercises'] = RoundExerciseFormSet(view.request.POST or None)
    return context


def _save_round(view, form):
    """Save the round and its inline exercises, then keep the M2M (used by
    get_total()/get_row()) in sync with the FK-linked exercise rows."""
    context = view.get_context_data()
    exercises = context['exercises']
    if not exercises.is_valid():
        return view.form_invalid(form)
    with transaction.atomic():
        view.object = form.save()
        exercises.instance = view.object
        exercises.save()
        view.object.exercises.set(view.object.back_round.all())
    return HttpResponseRedirect(view.get_success_url())


class RoundCreateView(FullPageCreateView):
    model = Round
    form_class = RoundForm
    template_name = 'round_form.html'
    success_url = reverse_lazy('round:round_list')
    success_message = _('round created.')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        event_id = self.request.GET.get('event_id')
        if event_id:
            initial['refer_event'] = get_object_or_404(Event, pk=event_id)
        return initial

    def get_context_data(self, **kwargs):
        return _add_exercise_formset(self, super().get_context_data(**kwargs))

    def form_valid(self, form):
        return _save_round(self, form)


class RoundListView(GenericListView):
    model = Round


class RoundUpdateView(FullPageUpdateView):
    model = Round
    form_class = RoundForm
    template_name = 'round_form.html'
    success_url = reverse_lazy('round:round_list')
    success_message = _('round updated.')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        return _add_exercise_formset(self, super().get_context_data(**kwargs))

    def form_valid(self, form):
        return _save_round(self, form)


class RoundDetailView(GenericDetailView):
    model = Round


class RoundDeleteView(FullPageDeleteView):
    model = Round
    success_url = reverse_lazy('round:round_list')
    success_message = _('round deleted.')
