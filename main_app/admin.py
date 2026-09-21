from django.contrib import admin
from .models import Game, Field, Question, Group, GameSession

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'created_by', 'mode', 'is_active']

@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ['game', 'position', 'field_type', 'label']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['field', 'question_text', 'question_type', 'points']

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'teacher', 'is_active', 'created_at']
    filter_horizontal = ['students']

@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ['student', 'game', 'group', 'score', 'is_finished', 'started_at']
