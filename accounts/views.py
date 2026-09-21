from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .forms import StudentRegistrationForm, TeacherRegistrationForm
from .models import Profile
from main_app.models import Game, Group, GameSession
from .forms import ProfileEditForm


def register_student(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            profile = form.save()
            # Автоматично логваме студента
            user = profile.user
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Регистрацията е успешна! Влезли сте като студент.')
            return redirect('main_app:index')
    else:
        form = StudentRegistrationForm()
    return render(request, 'accounts/register_student.html', {'form': form})

def register_teacher(request):
    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Регистрацията е успешна! Чакате одобрение от администратор.')
            return redirect('login')
    else:
        form = TeacherRegistrationForm()
    return render(request, 'accounts/register_teacher.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Опитваме първо със студентски бекенд
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Проверка дали е преподавател и одобрен
            if user.profile.role == 'TEACHER' and not user.profile.is_approved:
                logout(request)
                messages.error(request, 'Вашият профил все още не е одобрен от администратор.')
                return redirect('login')
            return redirect('main_app:index')
        else:
            messages.error(request, 'Грешно потребителско име или парола.')
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('main_app:index')

@staff_member_required
def approve_teachers(request):
    pending_teachers = Profile.objects.filter(role='TEACHER', is_approved=False)
    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        profile = Profile.objects.get(id=teacher_id)
        profile.is_approved = True
        profile.save()
        messages.success(request, f'Преподавателят {profile.user.get_full_name()} е одобрен.')
        return redirect('approve_teachers')
    return render(request, 'accounts/approve_teachers.html', {'pending_teachers': pending_teachers})

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Profile
from main_app.models import Game, Group, GameSession

@login_required
def profile_view(request):
    user = request.user
    profile = user.profile
    role = profile.role

    context = {
        'user': user,
        'profile': profile,
        'role': role,
    }

    # Допълнителна информация според ролята
    if role == 'STUDENT':
        # Игри, в които студентът участва
        sessions = GameSession.objects.filter(student=user).select_related('game')
        # Групи, в които е член
        groups = user.student_groups.all()
        context['sessions'] = sessions
        context['groups'] = groups

    elif role == 'TEACHER':
        # Групи, които преподавателят води
        groups = Group.objects.filter(teacher=user)
        # Игри, които е създал
        games = Game.objects.filter(created_by=user)
        context['groups'] = groups
        context['games'] = games

    elif role == 'ADMIN' or user.is_superuser:
        # Статистика за администратора
        from django.contrib.auth.models import User
        context['total_users'] = User.objects.count()
        context['total_teachers'] = Profile.objects.filter(role='TEACHER', is_approved=True).count()
        context['total_students'] = Profile.objects.filter(role='STUDENT').count()
        context['total_games'] = Game.objects.count()
        context['pending_teachers'] = Profile.objects.filter(role='TEACHER', is_approved=False).count()

    return render(request, 'accounts/profile.html', context)
@login_required
def edit_profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профилът беше обновен успешно.')
            return redirect('accounts:profile')
    else:
        form = ProfileEditForm(instance=profile, user=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})

def register_choice(request):
    """Страница за избор на тип регистрация."""
    return render(request, 'accounts/register_choice.html')