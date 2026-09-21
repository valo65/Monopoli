# main_app/views.py

import random

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Game, Field, GameSession, Question, StudentAnswer
from .forms import GameForm, FieldForm
from .serializers import GameSerializer, FieldSerializer
from .ai_utils import check_open_answer


# ============================================================
# ОСНОВНИ СТРАНИЦИ
# ============================================================

def index(request):
    return render(request, 'main_app/index.html', {'title': 'Начало'})


def about(request):
    return render(request, 'main_app/about.html', {'title': 'За нас'})


def contact(request):
    return render(request, 'main_app/contact.html', {'title': 'Контакти'})


# ============================================================
# REST API VIEWSETS
# ============================================================

class GameViewSet(viewsets.ModelViewSet):
    queryset = Game.objects.filter(is_active=True)
    serializer_class = GameSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class FieldViewSet(viewsets.ModelViewSet):
    queryset = Field.objects.all()
    serializer_class = FieldSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


# ============================================================
# СЪЗДАВАНЕ НА ИГРА (само за преподаватели)
# ============================================================

@login_required
def create_game(request):
    """Създаване на нова игра от преподавател."""
    if request.user.profile.role != 'TEACHER' or not request.user.profile.is_approved:
        messages.error(request, 'Само одобрени преподаватели могат да създават игри.')
        return redirect('main_app:index')

    if request.method == 'POST':
        form = GameForm(request.POST, request.FILES)
        if form.is_valid():
            game = form.save(commit=False)
            game.created_by = request.user
            game.save()
            messages.success(request, f'Играта "{game.title}" е създадена! Сега добавете полета.')
            return redirect('main_app:add_fields', game_id=game.id)
    else:
        form = GameForm()

    return render(request, 'main_app/create_game.html', {'form': form})


@login_required
def add_fields(request, game_id):
    """Добавяне на полета към вече създадена игра."""
    game = get_object_or_404(Game, id=game_id, created_by=request.user)

    if request.method == 'POST':
        form = FieldForm(request.POST, request.FILES)
        if form.is_valid():
            field = form.save(commit=False)
            field.game = game
            field.save()
            messages.success(request, f'Поле {field.position} е добавено!')
            return redirect('main_app:add_fields', game_id=game.id)
    else:
        form = FieldForm()

    fields = game.fields.all().order_by('position')
    return render(request, 'main_app/add_fields.html', {
        'game': game,
        'form': form,
        'fields': fields,
    })


# ============================================================
# ИГРА (САМО ЕДНА ДЕФИНИЦИЯ!)
# ============================================================

@login_required
def play_game(request, game_id):
    """Стартиране на игра – показване на игровото поле."""
    game = get_object_or_404(Game, id=game_id, is_active=True)
    fields = game.fields.all().order_by('position')

    # Вземаме или създаваме сесия за текущия студент
    session, created = GameSession.objects.get_or_create(
        game=game,
        student=request.user,
        defaults={'current_position': 0}
    )

    board = get_board_layout(fields)

    return render(request, 'main_app/play_game.html', {
        'game': game,
        'fields': fields,
        'session': session,
        'board': board,
    })


# ============================================================
# ХВЪРЛЯНЕ НА ЗАР
# ============================================================
@require_POST
@login_required
def roll_dice(request, session_id):
    session = get_object_or_404(GameSession, id=session_id, student=request.user)

    if session.is_finished:
        return JsonResponse({'error': 'Играта е завършена.'}, status=400)

    dice_value = random.randint(1, 6)
    old_position = session.current_position
    new_position = old_position + dice_value

    total_fields = 32
    if new_position >= total_fields:
        new_position = total_fields
        session.is_finished = True

    session.current_position = new_position
    session.save()

    field = Field.objects.filter(game=session.game, position=new_position).first()
    field_data = None
    if field:
        field_data = {
            'position': field.position,
            'type': field.field_type,
            'type_display': field.get_field_type_display(),
            'label': field.label,
            'material_title': field.material_title,
            'material_content': field.material_content,
            'material_image': field.material_image.url if field.material_image else None,
            'material_link': field.material_link,
            'has_questions': field.questions.exists(),
        }

    return JsonResponse({
        'dice': dice_value,
        'old_position': old_position,
        'new_position': new_position,
        'is_finished': session.is_finished,
        'field': field_data,
    })

# ============================================================
# ОТГОВОР НА ВЪПРОС (с ИИ проверка)
# ============================================================

@require_POST
@login_required
def answer_question(request, question_id):
    """Обработва отговора на студент и връща JSON с резултата."""
    question = get_object_or_404(Question, id=question_id)
    student_answer = request.POST.get('answer', '').strip()

    if not student_answer:
        return JsonResponse({'error': 'Моля, въведете отговор.'}, status=400)

    # Намираме активната сесия на студента
    session = GameSession.objects.filter(
        student=request.user,
        game=question.field.game,
        is_finished=False
    ).first()

    if not session:
        return JsonResponse({'error': 'Няма активна сесия.'}, status=400)

    # Проверка на отговора според типа
    if question.question_type == 'MC':
        # Множествен избор – сравняваме номерата
        is_correct = student_answer in question.correct_options.split(',')
        similarity = 1.0 if is_correct else 0.0
        message = '✅ Верен отговор!' if is_correct else '❌ Грешен отговор.'
    else:
        # Отворен отговор – използваме ИИ
        result = check_open_answer(student_answer, question.correct_answer)
        is_correct = result['is_correct']
        similarity = result['similarity']
        message = result['message']

    # Записваме отговора
    points = question.points if is_correct else 0
    StudentAnswer.objects.create(
        session=session,
        question=question,
        student_answer=student_answer,
        similarity_score=similarity,
        is_correct=is_correct,
        points_earned=points,
    )

    # Обновяваме резултата в сесията
    if is_correct:
        session.score += points
        session.save()

    return JsonResponse({
        'is_correct': is_correct,
        'similarity': round(similarity, 2),
        'message': message,
        'points_earned': points,
        'total_score': session.score,
    })

def get_board_layout(fields):
    """
    Генерира 10×10 мрежа за игралното поле.
    Позиции 1-32 = полета (32 общо, 8 групи × 4)
    Позиция 0 = START (TR ъгъл)
    Ъглите (TL, BL, BR) са декоративни.
    """
    # Речник {position: field} за бърз достъп
    fields_by_pos = {f.position: f for f in fields}

    board = []
    for row in range(1, 11):
        for col in range(1, 11):
            cell = {
                'row': row, 'col': col,
                'type': None, 'position': None,
                'group': None, 'field': None,
            }

            # === ЪГЛИ ===
            if (row, col) == (1, 10):
                cell['type'] = 'START'
            elif (row, col) in [(1, 1), (10, 1), (10, 10)]:
                cell['type'] = 'CORNER'

            # === ТОП РЕД (дясно → ляво): позиции 1-8 ===
            elif row == 1 and 2 <= col <= 9:
                pos = 10 - col       # col 9 → pos 1, col 2 → pos 8
                cell['type'] = 'FIELD'
                cell['position'] = pos

            # === ЛЯВА КОЛОНА (горе → долу): позиции 9-16 ===
            elif col == 1 and 2 <= row <= 9:
                pos = row + 7        # row 2 → pos 9, row 9 → pos 16
                cell['type'] = 'FIELD'
                cell['position'] = pos

            # === ДОЛЕН РЕД (ляво → дясно): позиции 17-24 ===
            elif row == 10 and 2 <= col <= 9:
                pos = col + 15       # col 2 → pos 17, col 9 → pos 24
                cell['type'] = 'FIELD'
                cell['position'] = pos

            # === ДЯСНА КОЛОНА (долу → горе): позиции 25-32 ===
            elif col == 10 and 2 <= row <= 9:
                pos = 34 - row       # row 9 → pos 25, row 2 → pos 32
                cell['type'] = 'FIELD'
                cell['position'] = pos

            # === ЦЕНТЪР ===
            elif 2 <= row <= 9 and 2 <= col <= 9:
                cell['type'] = 'CENTER'

            # Прикачаме полето и групата
            if cell['position']:
                cell['field'] = fields_by_pos.get(cell['position'])
                cell['group'] = (cell['position'] - 1) // 4 + 1

            board.append(cell)

    return board