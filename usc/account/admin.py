from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import RegisterForm
from .models import Profile, UsedResetToken, User


class UserAdmin(BaseUserAdmin):
    add_form = RegisterForm
    list_display = ('email', 'active',)
    list_filter = ('active', 'staff', 'admin',)
    search_fields = ['email']
    fieldsets = (
        ('User', {'fields': ('email', 'password')}),
        ('Permissions', {
         'fields': ('admin', 'staff', 'active', 'verified_email',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password',)
        }
        ),
    )
    ordering = ('email',)
    filter_horizontal = ()


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('get_fullname', 'phone', 'country', 'city', 'state',)
    list_filter = ('gender',)

    filter_horizontal = ()


admin.site.register(User, UserAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(UsedResetToken)
