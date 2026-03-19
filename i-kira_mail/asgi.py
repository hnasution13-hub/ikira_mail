"""
ASGI config for i-kira_mail project.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'i-kira_mail.settings')
application = get_asgi_application()