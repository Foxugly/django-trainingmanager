from django.contrib import admin
from member.models import Member
# Register your models here.


class MemberAdmin(admin.ModelAdmin):
    pass

admin.site.register(Member, MemberAdmin)