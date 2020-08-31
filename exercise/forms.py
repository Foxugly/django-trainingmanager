from django.forms import ModelForm

from exercise.models import Exercise


class BSExerciseForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(BSExerciseForm, self).__init__(*args, **kwargs)  # Call to ModelForm constructor
        self.fields['order'].widget.attrs['style'] = 'width:90px'
        self.fields['repetition'].widget.attrs['style'] = 'width:90px'
        self.fields['distance'].widget.attrs['style'] = 'width:90px'
        self.fields['t_start'].widget.attrs['style'] = 'width:90px'
        self.fields['t_break'].widget.attrs['style'] = 'width:90px'
        self.fields['notes'].widget.attrs['style'] = 'width:800px'

    class Meta:
        model = Exercise
        fields = ['order', 'repetition', 'distance', 'stroke', 'energysegment', 'notes', 't_start', 't_break', ]


class ExerciseForm(ModelForm):
    class Meta:
        model = Exercise
        fields = ['order', 'repetition', 'distance', 'stroke', 'energysegment', 'notes', 't_start', 't_break', ]
