from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

UserModel = get_user_model()

class EmailAuthBackend(ModelBackend):
    """
    Custom authentication backend yang mengizinkan login dengan email
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Coba cari user berdasarkan email
            user = UserModel.objects.get(Q(email__iexact=username) | Q(username__iexact=username))
        except UserModel.DoesNotExist:
            return None
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None