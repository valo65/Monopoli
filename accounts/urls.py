from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/student/', views.register_student, name='register_student'),
    path('register/teacher/', views.register_teacher, name='register_teacher'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('approve-teachers/', views.approve_teachers, name='approve_teachers'),
    path('profile/', views.profile_view, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('register/', views.register_choice, name='register_choice'),
]

