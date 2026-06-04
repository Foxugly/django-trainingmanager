from django.forms import DateInput, ModelForm

from event.models import Event


class EventForm(ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'goal', 'color', 'date', 'hour_start', 'hour_end']
        widgets = {
            'date': DateInput(format='%Y-%m-%d',
                              attrs={'class': 'form-control', 'type': 'date'}),
            'hour_start': DateInput(format='%H:%M',
                                    attrs={'class': 'form-control', 'type': 'time'}),
            'hour_end': DateInput(format='%H:%M',
                                  attrs={'class': 'form-control', 'type': 'time'}),
        }
