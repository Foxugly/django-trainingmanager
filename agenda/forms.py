from django.forms import DateInput, ModelForm

from agenda.models import Agenda


class AgendaForm(ModelForm):
    class Meta:
        model = Agenda
        # events/members are managed elsewhere (calendar, attendance), not on the
        # create/edit form.
        exclude = ['events', 'members']
        widgets = {
            'date_start': DateInput(format='%Y-%m-%d',
                                    attrs={'class': 'form-control', 'type': 'date'}),
            'date_end': DateInput(format='%Y-%m-%d',
                                  attrs={'class': 'form-control', 'type': 'date'}),
        }
