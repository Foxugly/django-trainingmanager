from django.forms import ModelForm

from member.models import Member


class MemberForm(ModelForm):
    class Meta:
        model = Member
        fields = ['firstname', 'lastname', 'phonenumber', 'email']
