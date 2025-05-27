"""Админка для пользователей."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Subscription


class UserAdmin(BaseUserAdmin):
    """Админка для пользователей."""

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active')


admin.site.register(User, UserAdmin)
admin.site.register(Subscription)
