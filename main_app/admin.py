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
    list_display = ['name', 'game', 'created_by', 'is_active', 'is_started', 'created_at']
    list_filter = ['is_active', 'is_started', 'created_at']
    search_fields = ['name', 'join_code']
    filter_horizontal = ['students']
    readonly_fields = ['join_code', 'created_at']

@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ['student', 'game', 'group', 'score', 'is_finished', 'started_at']

from .models import Material, Bank, FieldOwnership, Turn


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['order', 'title', 'game']
    list_filter = ['game']
    ordering = ['game', 'order']


@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    list_display = ['group', 'balance']


@admin.register(FieldOwnership)
class FieldOwnershipAdmin(admin.ModelAdmin):
    list_display = ['field', 'owner', 'session', 'purchased_at']
    list_filter = ['purchased_at']


@admin.register(Turn)
class TurnAdmin(admin.ModelAdmin):
    list_display = ['turn_number', 'session', 'dice_value', 'from_position', 'to_position', 'created_at']
    list_filter = ['created_at']