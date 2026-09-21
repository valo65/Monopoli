from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    ROLES = (
        ('ADMIN', 'Администратор'),
        ('TEACHER', 'Преподавател'),
        ('STUDENT', 'Студент'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLES, default='STUDENT')

    # За студент
    faculty_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    group = models.CharField(max_length=20, blank=True, null=True)

    # За преподавател
    is_approved = models.BooleanField(default=False)  # чака одобрение от администратор

    # Общи
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()})"

# Сигнал: автоматично създаване на Profile при създаване на User
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()