from bootstrap_modal_forms.generic import BSModalCreateView, BSModalUpdateView, BSModalDeleteView
from django.db import transaction
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404
from round.forms import BSRoundForm, RoundExerciseFormSet
from round.models import Round
from tools.generic_views import *
from event.models import Event


class RoundCreateView(BSModalCreateView):
    model = Round
    fields = None
    form_class = BSRoundForm
    template_name = 'modal_round.html'
    success_message = 'Success: created.'
    success_url = reverse_lazy('round:round_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(RoundCreateView, self).get_context_data(**kwargs)
        context.update({'add_exercise': _("Ajouter un exercice")})
        context.update({'delete_exercise': _("supprimer")})
        if self.request.POST:
            context['exercises'] = RoundExerciseFormSet(self.request.POST)
        else:
            context['exercises'] = RoundExerciseFormSet()
        return context

    def get_initial(self):
        initial = super().get_initial()
        if self.request.GET.get('event_id'):
            initial['refer_event'] = get_object_or_404(Event, pk=self.request.GET['event_id'])
        return initial

    def form_valid(self, form):
        print("round:form_valid")
        if not self.request.is_ajax():
            with transaction.atomic():
                f = form.save(commit=False)
                f.save()
                context = self.get_context_data()
                exercises = context['exercises']
                for exform in exercises:
                    print("exform")
                    if exform.is_valid():
                        ex = exform.save(commit=False)
                        ex.refer_round = f
                        ex.save()
                        f.exercises.add(ex) if ex not in f.exercises.all() else None
        return super().form_valid(form)

    def get_success_url(self):
        if "next" in self.request.GET:
            return self.request.GET["next"]
        else:
            return self.success_url


class RoundListView(GenericListView):
    model = Round


class RoundUpdateView(BSModalUpdateView):
    model = Round
    fields = None
    form_class = BSRoundForm
    template_name = 'modal_round.html'
    success_message = 'Success: created.'
    success_url = reverse_lazy('round:round_list')

    def get_success_url(self):
        if "next" in self.request.GET:
            return self.request.GET["next"]
        else:
            return self.success_url

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super(RoundUpdateView, self).get_context_data(**kwargs)
        context.update({'add_exercise': _("Ajouter un exercice")})
        context.update({'delete_exercise': _("supprimer")})
        if self.request.POST:
            context['exercises'] = RoundExerciseFormSet(self.request.POST)
        else:
            context['exercises'] = RoundExerciseFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        exercises = context['exercises']
        with transaction.atomic():
            self.object = form.save()
        if exercises.is_valid():
            exercises.instance = self.object
            exercises.save()
        return super(RoundUpdateView, self).form_valid(form)

    def get_success_url(self):
        if "next" in self.request.GET:
            return self.request.GET["next"]
        else:
            return self.success_url


class RoundDetailView(GenericDetailView):
    model = Round


class RoundDeleteView(BSModalDeleteView):
    model = Round
    template_name = 'delete.html'
    success_message = 'Success: removed.'
    success_url = reverse_lazy('round:round_list')

    def get_success_url(self):
        if "next" in self.request.GET:
            return self.request.GET["next"]
        else:
            return self.success_url
