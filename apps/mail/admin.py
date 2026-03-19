from django.contrib import admin
from .models import Email, Attachment, Contact, EmailFolder


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    readonly_fields = ['filename', 'content_type', 'size', 'created_at']


@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ['subject', 'sender', 'recipients', 'folder', 'is_read', 'created_at']
    list_filter = ['folder', 'is_read', 'is_starred']
    search_fields = ['subject', 'recipients', 'sender__email']
    inlines = [AttachmentInline]
    readonly_fields = ['created_at', 'sent_at']


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'email', 'content_type', 'size', 'created_at']
    search_fields = ['filename', 'email__subject']


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'company', 'user']
    search_fields = ['name', 'email']
