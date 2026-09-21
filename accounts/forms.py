from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile
import random
import string

class StudentRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, label='Име')
    last_name = forms.CharField(max_length=30, label='Фамилия')
    email = forms.EmailField(label='Имейл')
    group = forms.CharField(max_length=20, label='Група')

    class Meta:
        model = Profile
        fields = ['faculty_number', 'group']

    def clean_faculty_number(self):
        faculty_number = self.cleaned_data.get('faculty_number')
        if Profile.objects.filter(faculty_number=faculty_number).exists():
            raise forms.ValidationError('Този факултетен номер вече е регистриран.')
        return faculty_number

    def save(self, commit=True):
        """
        Създава User и обновява автоматично създадения Profile (от сигнала).
        """
        faculty_number = self.cleaned_data['faculty_number']

        # 1. Създаваме User (сигналът автоматично ще създаде Profile)
        user = User.objects.create_user(
            username=faculty_number,
            email=self.cleaned_data['email'],
            password=None,  # без парола
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
        )
        user.set_unusable_password()
        user.save()

        # 2. Вземаме вече създадения Profile и го обновяваме
        profile = user.profile  # 👈 ВАЖНО: не създаваме нов, а ползваме съществуващия
        profile.faculty_number = faculty_number
        profile.group = self.cleaned_data['group']
        profile.role = 'STUDENT'

        if commit:
            profile.save()

        return profile

class TeacherRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, label='Име')
    last_name = forms.CharField(max_length=30, label='Фамилия')
    email = forms.EmailField(label='Имейл')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'first_name', 'last_name']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # username = email
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile = Profile.objects.get(user=user)
            profile.role = 'TEACHER'
            profile.is_approved = False
            profile.save()
        return user



class ProfileEditForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, label='Име')
    last_name = forms.CharField(max_length=30, label='Фамилия')
    email = forms.EmailField(label='Имейл')

    class Meta:
        model = Profile
        fields = ['phone', 'group']  # за студенти – група
        # за преподаватели и админи – само телефон

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

            # Студентите могат да променят група
            if user.profile.role != 'STUDENT':
                self.fields.pop('group', None)

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile.save()
        return profile