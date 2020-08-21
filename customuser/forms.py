from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.forms import ModelForm
from customuser.models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("username",)


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = '__all__'


class CustomUserForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(CustomUserForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.fields['is_staff'].widget.attrs['readonly'] = True
            self.fields['is_staff'].widget.attrs['disabled'] = 'disabled'
            self.fields['is_foo_admin'].widget.attrs['readonly'] = True
            self.fields['is_foo_admin'].widget.attrs['disabled'] = 'disabled'
            self.fields['is_superuser'].widget.attrs['readonly'] = True
            self.fields['is_superuser'].widget.attrs['disabled'] = 'disabled'

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'language', 'is_staff', 'is_foo_admin', 'is_superuser', ]
