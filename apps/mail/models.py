from django.db import models
from django.conf import settings
from django.utils import timezone
import os

class Email(models.Model):
    FOLDER_CHOICES = [
        ('inbox', 'Inbox'),
        ('sent', 'Sent'),
        ('drafts', 'Drafts'),
        ('trash', 'Trash'),
        ('spam', 'Spam'),
        ('archive', 'Archive'),
        ('outbox', 'Outbox'),  # FIX: tambah outbox
    ]
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_emails'
    )
    recipients = models.TextField(help_text="Email recipients, separated by commas")
    cc = models.TextField(blank=True, help_text="CC recipients")
    bcc = models.TextField(blank=True, help_text="BCC recipients")
    
    subject = models.CharField(max_length=255)
    body_text = models.TextField(blank=True)
    body_html = models.TextField(blank=True)
    
    folder = models.CharField(max_length=20, choices=FOLDER_CHOICES, default='inbox')
    is_read = models.BooleanField(default=False)
    is_starred = models.BooleanField(default=False)
    is_important = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(default=timezone.now)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    in_reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies'
    )
    
    message_id = models.CharField(max_length=255, blank=True)
    thread_id = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipients']),
            models.Index(fields=['sender', 'folder']),
            models.Index(fields=['thread_id']),
        ]
    
    def __str__(self):
        return f"{self.sender.email} -> {self.recipients}: {self.subject}"
    
    def get_recipient_list(self):
        return [r.strip() for r in self.recipients.split(',') if r.strip()]
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])


class Attachment(models.Model):
    email = models.ForeignKey(Email, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='attachments/%Y/%m/%d/')
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size = models.IntegerField(help_text="File size in bytes")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.filename
    
    def delete(self, *args, **kwargs):
        """Hapus file fisik (local) atau Cloudinary resource"""
        if self.file:
            try:
                # Hanya hapus file lokal; Cloudinary cleanup via dashboard/signal
                if hasattr(self.file, 'path') and os.path.isfile(self.file.path):
                    os.remove(self.file.path)
            except (NotImplementedError, ValueError):
                # Cloudinary storage tidak support .path - skip
                pass
        super().delete(*args, **kwargs)


class Contact(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contacts')
    email = models.EmailField()
    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'email']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} <{self.email}>"


class EmailFolder(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='custom_folders')
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'name']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"
