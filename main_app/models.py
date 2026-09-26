from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

class Article(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='articles')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='articles')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Game(models.Model):
    MODE_CHOICES = (
        ('LEARN', 'Запознаване с материал'),
        ('PRACTICE', 'Затвърждаване'),
        ('EXAM', 'Изпит'),
    )

    title = models.CharField(max_length=200, verbose_name="Име на играта")
    subject = models.CharField(max_length=100, verbose_name="Дисциплина/Тема")
    description = models.TextField(blank=True, verbose_name="Описание")
    center_image = models.ImageField(upload_to='game_images/', blank=True, null=True, verbose_name="Централна картинка")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_games', verbose_name="Създател")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='LEARN', verbose_name="Режим на игра")
    current_material_index = models.PositiveIntegerField(default=0, verbose_name="Текущ материал")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Игра"
        verbose_name_plural = "Игри"

class Field(models.Model):
    """Квадратче от игралното поле."""
    FIELD_TYPES = (
        ('START', 'Старт'),
        ('QUESTION', 'Въпрос'),
        ('BONUS', 'Бонус'),
        ('PENALTY', 'Наказание'),
        ('FINISH', 'Финал'),
        ('INFO', 'Информация'),
    )

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='fields', verbose_name="Игра")
    position = models.PositiveIntegerField(verbose_name="Позиция (номер на квадратчето)")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, default='QUESTION', verbose_name="Тип на поле")
    label = models.CharField(max_length=100, blank=True, verbose_name="Етикет (име на полето)")
    # Обучаващ материал – може да е текст, връзка, код, картинка и т.н.
    material_title = models.CharField(max_length=200, blank=True, verbose_name="Заглавие на материала")
    material_content = models.TextField(blank=True, verbose_name="Съдържание на материала")
    material_image = models.ImageField(upload_to='field_materials/', blank=True, null=True, verbose_name="Картинка към материала")
    material_link = models.URLField(blank=True, verbose_name="Връзка към допълнителен материал")

    def __str__(self):
        return f"{self.game.title} - Поле {self.position}"

    class Meta:
        ordering = ['position']
        verbose_name = "Поле"
        verbose_name_plural = "Полета"

class Question(models.Model):
    QUESTION_TYPES = (
        ('MC', 'Множествен избор (4 отговора)'),
        ('OPEN', 'Отворен отговор'),
    )
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name='questions', verbose_name="Свързано поле")
    question_text = models.TextField(verbose_name="Текст на въпроса")
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='MC', verbose_name="Тип въпрос")
    # За MC въпроси:
    option1 = models.CharField(max_length=255, blank=True, verbose_name="Отговор 1")
    option2 = models.CharField(max_length=255, blank=True, verbose_name="Отговор 2")
    option3 = models.CharField(max_length=255, blank=True, verbose_name="Отговор 3")
    option4 = models.CharField(max_length=255, blank=True, verbose_name="Отговор 4")
    # Кои отговори са верни (за MC може да има 1 или 2 верни)
    correct_options = models.CharField(max_length=10, blank=True, help_text="Номера на верните отговори, разделени със запетая (напр. 1,3)", verbose_name="Верни отговори")
    # За отворен отговор:
    correct_answer = models.TextField(blank=True, verbose_name="Верен отговор (за отворен въпрос)")
    # Точкуване
    points = models.PositiveIntegerField(default=1, verbose_name="Точки за верен отговор")
    # За изпит – може да има тежест
    weight = models.PositiveIntegerField(default=1, verbose_name="Тежест (за изпит)")

    def __str__(self):
        return f"Въпрос към поле {self.field.position} - {self.question_text[:50]}"

class Group(models.Model):
    """Група от студенти за игра."""
    name = models.CharField(max_length=100, verbose_name="Име на групата")
    game = models.ForeignKey(
        Game, on_delete=models.CASCADE,
        related_name='groups', verbose_name="Игра"
    )
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='created_groups', verbose_name="Създател"
    )
    students = models.ManyToManyField(
        User, related_name='student_groups',
        blank=True, verbose_name="Студенти"
    )
    join_code = models.CharField(
        max_length=8, unique=True, blank=True,
        verbose_name="Код за присъединяване"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    is_started = models.BooleanField(default=False, verbose_name="Стартирала")
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.join_code:
            import random
            import string
            self.join_code = ''.join(
                random.choices(string.ascii_uppercase + string.digits, k=6)
            )
        super().save(*args, **kwargs)

    def is_teacher_group(self):
        return self.created_by.profile.role == 'TEACHER'

    def can_start_game(self, user):
        if user == self.created_by and self.is_teacher_group():
            return True
        if not self.is_teacher_group() and user in self.students.all():
            return True
        if user == self.game.created_by:
            return True
        return False

    def __str__(self):
        return f"{self.name} – {self.game.title}"

    class Meta:
        verbose_name = "Група"
        verbose_name_plural = "Групи"

class GameSession(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='sessions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='game_sessions')
    group = models.ForeignKey('Group', on_delete=models.CASCADE, null=True, blank=True)  # ако има групи
    current_position = models.PositiveIntegerField(default=0)
    score = models.PositiveIntegerField(default=0)
    is_finished = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    turn_order = models.PositiveIntegerField(default=0, verbose_name="Ред на хвърляне")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    def __str__(self):
        return f"{self.student.username} - {self.game.title}"


class StudentAnswer(models.Model):
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    student_answer = models.TextField()
    similarity_score = models.FloatField(default=0.0)
    is_correct = models.BooleanField(default=False)
    points_earned = models.PositiveIntegerField(default=0)
    answered_at = models.DateTimeField(auto_now_add=True)
# ============================================================
# УЧЕБНИ МАТЕРИАЛИ
# ============================================================

class Material(models.Model):
    """Учебен материал с въпрос след него."""
    game = models.ForeignKey(
        Game, on_delete=models.CASCADE,
        related_name='materials', verbose_name="Игра"
    )
    order = models.PositiveIntegerField(verbose_name="Пореден номер")

    # Съдържание
    title = models.CharField(max_length=200, verbose_name="Заглавие")
    content = models.TextField(blank=True, verbose_name="Съдържание")
    formula = models.TextField(blank=True, verbose_name="Формули")
    image = models.ImageField(
        upload_to='materials/', blank=True, null=True,
        verbose_name="Изображение"
    )
    video_url = models.URLField(blank=True, verbose_name="Видео URL")

    # Въпрос след материала
    question_text = models.TextField(verbose_name="Текст на въпроса")
    option1 = models.CharField(max_length=255, verbose_name="Отговор 1")
    option2 = models.CharField(max_length=255, verbose_name="Отговор 2")
    option3 = models.CharField(max_length=255, verbose_name="Отговор 3")
    option4 = models.CharField(max_length=255, blank=True, verbose_name="Отговор 4")
    correct_options = models.CharField(
        max_length=10,
        help_text="Номера на верните отговори, разделени със запетая (напр. 1,3)",
        verbose_name="Верни отговори"
    )

    def __str__(self):
        return f"{self.order}. {self.title}"

    class Meta:
        ordering = ['order']
        verbose_name = "Материал"
        verbose_name_plural = "Материали"


# ============================================================
# БАНКА
# ============================================================

class Bank(models.Model):
    """Банка на играта – източник и приемник на точки."""
    group = models.OneToOneField(
        Group, on_delete=models.CASCADE,
        related_name='bank', verbose_name="Група"
    )
    balance = models.IntegerField(default=0, verbose_name="Баланс")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Банка на {self.group.name}: {self.balance} точки"

    class Meta:
        verbose_name = "Банка"
        verbose_name_plural = "Банки"


# ============================================================
# СОБСТВЕНОСТ НА ПОЛЕ
# ============================================================

class FieldOwnership(models.Model):
    """Собственост върху поле от игралното поле."""
    field = models.OneToOneField(
        Field, on_delete=models.CASCADE,
        related_name='ownership', verbose_name="Поле"
    )
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='owned_fields', verbose_name="Собственик"
    )
    session = models.ForeignKey(
        GameSession, on_delete=models.CASCADE,
        related_name='owned_fields', verbose_name="Сесия"
    )
    purchased_at = models.DateTimeField(auto_now_add=True)
    purchase_price = models.IntegerField(default=100, verbose_name="Цена на покупка")

    def __str__(self):
        return f"Поле {self.field.position} → {self.owner.username}"

    class Meta:
        verbose_name = "Собственост"
        verbose_name_plural = "Собствености"


# ============================================================
# ХОД НА ИГРАТА
# ============================================================

class Turn(models.Model):
    """Запис на всеки ход в играта."""
    session = models.ForeignKey(
        GameSession, on_delete=models.CASCADE,
        related_name='turns', verbose_name="Сесия"
    )
    turn_number = models.PositiveIntegerField(verbose_name="Номер на хода")
    dice_value = models.PositiveIntegerField(verbose_name="Стойност на зара")
    from_position = models.PositiveIntegerField(verbose_name="От позиция")
    to_position = models.PositiveIntegerField(verbose_name="До позиция")
    material = models.ForeignKey(
        Material, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Материал"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ход {self.turn_number} – {self.session.student.username}"

    class Meta:
        ordering = ['turn_number']
        verbose_name = "Ход"
        verbose_name_plural = "Ходове"