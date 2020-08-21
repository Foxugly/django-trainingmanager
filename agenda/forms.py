 
from django.forms import ModelForm, DateInput
from agenda.models import Agenda
from bootstrap_modal_forms.forms import BSModalModelForm


class AgendaForm(ModelForm):
    class Meta:
        model = Agenda
        exclude = []
        widgets = {
            'date_start': DateInput(
                format=('%d/%m/%Y'),
                attrs={'class': 'form-control', 
                       'placeholder': 'Select a date',
                       'type': 'date'
                      }),
            'date_end': DateInput(
                format=('%d/%m/%Y'),
                attrs={'class': 'form-control', 
                       'placeholder': 'Select a date',
                       'type': 'date'
                      }),
        }


class BSAgendaCreateForm(BSModalModelForm):
    class Meta:
        model = Agenda
        exclude = ['events', 'members']
        widgets = {
            'date_start': DateInput(
                format=('%d/%m/%Y'),
                attrs={'class': 'form-control', 
                       'placeholder': 'Select a date',
                       'type': 'date'
                      }),
            'date_end': DateInput(
                format=('%d/%m/%Y'),
                attrs={'class': 'form-control', 
                       'placeholder': 'Select a date',
                       'type': 'date'
                      }),
        }
