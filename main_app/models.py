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
    """Група от студенти, водена от преподавател."""
    name = models.CharField(max_length=100, verbose_name="Име на групата")
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teacher_groups', verbose_name="Преподавател")
    students = models.ManyToManyField(User, related_name='student_groups', verbose_name="Студенти")
    game = models.ForeignKey(Game, on_delete=models.SET_NULL, null=True, blank=True, related_name='groups', verbose_name="Активна игра")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    def __str__(self):
        return f"{self.name} (водена от {self.teacher.get_full_name()})"

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