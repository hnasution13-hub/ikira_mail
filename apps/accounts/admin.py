from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['email', 'username', 'first_name', 'last_name', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Informasi Tambahan', {
            'fields': ('company', 'phone', 'email_signature')
        }),
    )

admin.site.register(User, CustomUserAdmin)