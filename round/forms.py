from bootstrap_modal_forms.forms import BSModalModelForm
from django.forms import ModelForm, inlineformset_factory, HiddenInput

from exercise.forms import BSExerciseForm
from exercise.models import Exercise
from round.models import Round


class RoundForm(ModelForm):
    class Meta:
        model = Round
        fields = ['order', 'count', 't_start', 't_break', ]


class BSRoundForm(BSModalModelForm):

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(BSRoundForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Round
        fields = ['order', 'count', 't_start', 't_break', 'refer_event']
        widgets = {'refer_event': HiddenInput(), }


RoundExerciseFormSet = inlineformset_factory(Round, Exercise, form=BSExerciseForm, extra=1, can_delete=True)
