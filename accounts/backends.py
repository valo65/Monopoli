from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from .models import Profile

class FacultyNumberBackend(ModelBackend):
    """
    Позволява вход на студенти само с факултетен номер (без парола).
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            profile = Profile.objects.get(faculty_number=username, role='STUDENT')
            return profile.user
        except Profile.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None