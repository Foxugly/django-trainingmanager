from bootstrap_modal_forms.forms import BSModalModelForm
from member.models import Member


class BSMemberForm(BSModalModelForm):
    class Meta:
        model = Member
        fields = ['firstname', 'lastname', 'phonenumber', 'email']
