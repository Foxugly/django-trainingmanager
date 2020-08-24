from bootstrap_modal_forms.forms import BSModalModelForm
from django.forms import DateInput, DateField

from event.models import Event


class BSEventForm(BSModalModelForm):

    class Meta:
        model = Event
        fields = ['name', 'goal', 'color', 'date', 'hour_start', 'hour_end']
        widgets = {
            'date': DateInput(
            format=('%d/%m/%Y'),
               attrs={'class': 'form-control',
                      'placeholder': 'Select a date',
                      'type': 'date'
                       }),
            'hour_start': DateInput(
                format=('%d/%m/%Y'),
                attrs={'class': 'form-control',
                       'placeholder': 'Select a date',
                       'type': 'time'
                       }),
            'hour_end': DateInput(
                format=('%d/%m/%Y'),
                attrs={'class': 'form-control',
                       'placeholder': 'Select a date',
                       'type': 'time'
                       }),
        }
