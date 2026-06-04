from django.forms import ModelForm

from exercise.models import Exercise


class ExerciseForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('order', 'repetition', 'distance', 't_start', 't_break'):
            self.fields[name].widget.attrs['style'] = 'width:90px'
        self.fields['notes'].widget.attrs['style'] = 'width:800px'

    class Meta:
        model = Exercise
        fields = ['order', 'repetition', 'distance', 'stroke', 'energysegment', 'notes', 't_start', 't_break', ]
