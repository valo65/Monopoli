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
from accounts.models import Profile


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
from .models import Group, GameSession
from django.contrib.auth.models import User


@login_required
def group_list(request):
    """Списък с групи – тези, в които потребителят участва или е създал."""
    if request.user.profile.role == 'TEACHER':
        groups = Group.objects.filter(created_by=request.user)
    else:
        groups = Group.objects.filter(students=request.user) | Group.objects.filter(created_by=request.user)

    return render(request, 'main_app/group_list.html', {'groups': groups.distinct()})


@login_required
def create_group(request):
    """Създаване на нова група."""
    if request.method == 'POST':
        name = request.POST.get('name')
        game_id = request.POST.get('game')

        if not name or not game_id:
            messages.error(request, 'Попълнете всички полета.')
        else:
            game = get_object_or_404(Game, id=game_id, is_active=True)
            group = Group.objects.create(
                name=name, game=game, created_by=request.user
            )
            # Създателят автоматично става член
            group.students.add(request.user)

            messages.success(request, f'Групата "{name}" е създадена! Код за присъединяване: {group.join_code}')
            return redirect('main_app:group_detail', group_id=group.id)

    games = Game.objects.filter(is_active=True)
    return render(request, 'main_app/create_group.html', {'games': games})


@login_required
def join_group(request):
    """Присъединяване към група чрез код."""
    if request.method == 'POST':
        code = request.POST.get('join_code', '').strip().upper()

        try:
            group = Group.objects.get(join_code=code, is_active=True)
            if request.user in group.students.all():
                messages.info(request, 'Вече сте член на тази група.')
            else:
                group.students.add(request.user)
                messages.success(request, f'Присъединихте се към "{group.name}"!')
            return redirect('main_app:group_detail', group_id=group.id)
        except Group.DoesNotExist:
            messages.error(request, 'Невалиден код за присъединяване.')

    return render(request, 'main_app/join_group.html')


@login_required
def group_detail(request, group_id):
    """Детайли за групата."""
    group = get_object_or_404(Group, id=group_id)

    # Проверка за достъп
    if request.user not in group.students.all() and request.user != group.created_by:
        messages.error(request, 'Нямате достъп до тази група.')
        return redirect('main_app:group_list')

    sessions = GameSession.objects.filter(group=group).select_related('student')

    return render(request, 'main_app/group_detail.html', {
        'group': group,
        'sessions': sessions,
        'can_start': group.can_start_game(request.user),
    })


@login_required
def add_students(request, group_id):
    """Преподавателят добавя студенти ръчно (с филтър по група)."""
    group = get_object_or_404(Group, id=group_id)

    # Само създателят (ако е преподавател) може да добавя
    if request.user != group.created_by or not group.is_teacher_group():
        messages.error(request, 'Нямате права да добавяте студенти.')
        return redirect('main_app:group_detail', group_id=group.id)

    if request.method == 'POST':
        student_ids = request.POST.getlist('students')
        for sid in student_ids:
            try:
                student = User.objects.get(id=sid, profile__role='STUDENT')
                group.students.add(student)
            except User.DoesNotExist:
                pass
        messages.success(request, f'{len(student_ids)} студенти добавени.')
        return redirect('main_app:group_detail', group_id=group.id)

    # Филтър по група
    group_filter = request.GET.get('group_filter', '').strip()
    students = User.objects.filter(profile__role='STUDENT')

    if group_filter:
        students = students.filter(profile__group__iexact=group_filter)

    # Махаме тези, които вече са в групата
    students = students.exclude(id__in=group.students.all().values_list('id', flat=True))

    # Списък с уникални групи за филтъра
    available_groups = Profile.objects.filter(
        role='STUDENT', group__isnull=False
    ).exclude(group='').values_list('group', flat=True).distinct()

    return render(request, 'main_app/add_students.html', {
        'group': group,
        'students': students,
        'available_groups': available_groups,
        'group_filter': group_filter,
    })


@login_required
def start_group_game(request, group_id):
    """Стартиране на играта за цялата група."""
    group = get_object_or_404(Group, id=group_id)

    if not group.can_start_game(request.user):
        messages.error(request, 'Нямате права да стартирате играта.')
        return redirect('main_app:group_detail', group_id=group.id)

    # Създаваме сесия за всеки член
    for student in group.students.all():
        GameSession.objects.get_or_create(
            game=group.game,
            student=student,
            group=group,
            defaults={'current_position': 0}
        )

    group.is_started = True
    group.save()

    messages.success(request, 'Играта е стартирана! Всички членове имат сесия.')
    return redirect('main_app:group_detail', group_id=group.id)
# ============================================================
# ПОКАЗВАНЕ НА МАТЕРИАЛ
# ============================================================

@login_required
def show_material(request, group_id):
    """
    Връща текущия материал за групата.
    След като го върне, увеличава индекса за следващия ход.
    Ако материалите свършат – започва отначало (зацикляне).
    """
    group = get_object_or_404(Group, id=group_id)
    game = group.game

    # Проверка за достъп
    if request.user not in group.students.all() and request.user != group.created_by:
        return JsonResponse({'error': 'Нямате достъп.'}, status=403)

    materials = game.materials.all().order_by('order')
    total = materials.count()

    if total == 0:
        return JsonResponse({
            'error': 'Няма въведени материали за тази игра.'
        }, status=400)

    # Взимаме текущия материал
    index = game.current_material_index % total
    material = materials[index]

    # Увеличаваме индекса за следващия ход
    game.current_material_index = (index + 1) % total
    game.save()

    # Връщаме данните
    return JsonResponse({
        'id': material.id,
        'order': material.order,
        'title': material.title,
        'content': material.content,
        'formula': material.formula,
        'image': material.image.url if material.image else None,
        'video_url': material.video_url,
        'question': {
            'text': material.question_text,
            'option1': material.option1,
            'option2': material.option2,
            'option3': material.option3,
            'option4': material.option4,
        },
        'total_materials': total,
        'current_index': index + 1,
    })
# ============================================================
# ОТГОВОР НА МАТЕРИАЛ (всички отговарят)
# ============================================================

@require_POST
@login_required
def submit_material_answer(request, material_id):
    """
    Записва отговора на студент на материал.
    Точкуване:
    - Верен (всички верни избрани) → +26
    - Частично верен (2 верни, избрал 1) → +13
    - Грешен → −13
    """
    material = get_object_or_404(Material, id=material_id)
    answer = request.POST.get('answer', '').strip()

    if not answer:
        return JsonResponse({'error': 'Моля, изберете отговор.'}, status=400)

    # Намираме сесията на студента
    session = GameSession.objects.filter(
        student=request.user,
        game=material.game,
        is_active=True
    ).first()

    if not session:
        return JsonResponse({'error': 'Няма активна сесия.'}, status=400)

    # Проверка на отговора
    correct = set(material.correct_options.split(','))
    selected = set(answer.split(','))

    if selected == correct:
        is_correct = True
        points = 26
        message = '✅ Верен отговор! +26 точки'
    elif selected.issubset(correct) and len(selected) > 0:
        is_correct = False
        points = 13
        message = '⚠️ Частично верен отговор. +13 точки'
    else:
        is_correct = False
        points = -13
        message = '❌ Грешен отговор. −13 точки'

    # Ако играчът е под -100 → без бонус за верен отговор
    if session.score < -100 and is_correct:
        points = 0
        message = '⚠️ Верен отговор, но сте под −100 точки. Без бонус.'

    # Записваме отговора
    StudentAnswer.objects.create(
        session=session,
        question=None,   # временно, защото Material не е Question
        student_answer=answer,
        similarity_score=1.0 if is_correct else 0.0,
        is_correct=is_correct,
        points_earned=points,
    )

    # Обновяваме резултата
    session.score += points
    session.save()

    # Банката поема разликата
    if session.group and hasattr(session.group, 'bank'):
        bank = session.group.bank
        bank.balance -= points
        bank.save()

    return JsonResponse({
        'is_correct': is_correct,
        'points': points,
        'message': message,
        'total_score': session.score,
    })