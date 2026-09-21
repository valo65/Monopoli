# main_app/serializers.py

from rest_framework import serializers
from .models import Game, Field, Question, Group, GameSession, StudentAnswer


class GameSerializer(serializers.ModelSerializer):
    created_by_username = serializers.ReadOnlyField(source='created_by.username')

    class Meta:
        model = Game
        fields = [
            'id', 'title', 'subject', 'description',
            'center_image', 'mode', 'is_active',
            'created_by', 'created_by_username', 'created_at'
        ]
        read_only_fields = ['created_by', 'created_at']


class FieldSerializer(serializers.ModelSerializer):
    game_title = serializers.ReadOnlyField(source='game.title')
    field_type_display = serializers.ReadOnlyField(source='get_field_type_display')

    class Meta:
        model = Field
        fields = [
            'id', 'game', 'game_title',
            'position', 'field_type', 'field_type_display', 'label',
            'material_title', 'material_content',
            'material_image', 'material_link'
        ]


class QuestionSerializer(serializers.ModelSerializer):
    field_position = serializers.ReadOnlyField(source='field.position')

    class Meta:
        model = Question
        fields = [
            'id', 'field', 'field_position',
            'question_text', 'question_type',
            'option1', 'option2', 'option3', 'option4',
            'correct_options', 'correct_answer',
            'points', 'weight'
        ]


class GroupSerializer(serializers.ModelSerializer):
    teacher_username = serializers.ReadOnlyField(source='teacher.username')
    game_title = serializers.ReadOnlyField(source='game.title')

    class Meta:
        model = Group
        fields = [
            'id', 'name', 'teacher', 'teacher_username',
            'students', 'game', 'game_title',
            'is_active', 'created_at'
        ]
        read_only_fields = ['created_at']


class GameSessionSerializer(serializers.ModelSerializer):
    student_username = serializers.ReadOnlyField(source='student.username')
    game_title = serializers.ReadOnlyField(source='game.title')

    class Meta:
        model = GameSession
        fields = [
            'id', 'game', 'game_title',
            'student', 'student_username',
            'group', 'current_position', 'score',
            'is_finished', 'started_at', 'updated_at'
        ]
        read_only_fields = ['started_at', 'updated_at']


class StudentAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.ReadOnlyField(source='question.question_text')

    class Meta:
        model = StudentAnswer
        fields = [
            'id', 'session', 'question', 'question_text',
            'student_answer', 'similarity_score',
            'is_correct', 'points_earned', 'answered_at'
        ]
        read_only_fields = ['answered_at']