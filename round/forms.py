from django.forms import HiddenInput, ModelForm, inlineformset_factory

from exercise.forms import ExerciseForm
from exercise.models import Exercise
from round.models import Round


class RoundForm(ModelForm):
    def __init__(self, *args, **kwargs):
        # The view passes the current user (legacy signature); the form doesn't
        # need it, so drop it before ModelForm validates the kwargs.
        kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Round
        fields = ['order', 'count', 't_start', 't_break', 'refer_event']
        widgets = {'refer_event': HiddenInput()}


RoundExerciseFormSet = inlineformset_factory(Round, Exercise, form=ExerciseForm, extra=1, can_delete=True)
