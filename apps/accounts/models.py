from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom User model dengan email sebagai identifier utama
    """
    email = models.EmailField(unique=True)
    company = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email_signature = models.TextField(blank=True, help_text="Tanda tangan email")
    
    # Set email sebagai field untuk login
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # username masih required untuk AbstractUser
    
    def __str__(self):
        return self.email
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'