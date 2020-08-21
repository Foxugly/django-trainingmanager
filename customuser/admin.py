from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from customuser.models import CustomUser
from customuser.forms import CustomUserChangeForm, CustomUserCreationForm
from django.utils.translation import gettext, gettext_lazy as _
from hijack_admin.admin import HijackUserAdminMixin


class CustomUserAdmin(UserAdmin, HijackUserAdminMixin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_superuser', 'is_foo_admin', 'hijack_field',)
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_foo_admin')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_foo_admin')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    filter_horizontal = ()


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.unregister(Group)
