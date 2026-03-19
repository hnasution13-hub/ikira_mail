"""
WSGI config for i-kira_mail project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'i-kira_mail.settings')
application = get_wsgi_application()