from django.contrib import admin

from .models import CustomUser


class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        'email',
        'username',
        'first_name',
        'last_name',
    )
    list_filter = ('email', 'username')


admin.site.register(CustomUser, CustomUserAdmin)
