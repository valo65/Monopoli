# main_app/ai_utils.py
"""
Модул за семантичен анализ на отворени отговори.
Използва модела all-MiniLM-L6-v2 от sentence-transformers.
"""

from sentence_transformers import SentenceTransformer, util

# Глобална променлива – моделът се зарежда само веднъж (lazy loading)
_model = None


def get_model():
    """
    Връща заредения модел. Ако още не е зареден – зарежда го.
    Това е бавна операция (~2-3 сек) и се прави само веднъж.
    """
    global _model
    if _model is None:
        print("Зареждане на ИИ модела all-MiniLM-L6-v2...")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Моделът е зареден успешно.")
    return _model


def semantic_similarity(text1: str, text2: str) -> float:
    """
    Изчислява косинусово сходство между два текста.
    Връща стойност между 0 и 1 (1 = идентични, 0 = напълно различни).
    """
    if not text1.strip() or not text2.strip():
        return 0.0

    model = get_model()
    emb1 = model.encode(text1, convert_to_tensor=True)
    emb2 = model.encode(text2, convert_to_tensor=True)
    cos_sim = util.cos_sim(emb1, emb2)
    return float(cos_sim[0][0].item())


def check_open_answer(student_answer: str,
                      correct_answer: str,
                      threshold: float = 0.75) -> dict:
    """
    Проверява дали отговорът на студента е семантично близък до верния.

    Параметри:
    - student_answer: текстът, въведен от студента
    - correct_answer: верният отговор, записан от преподавателя
    - threshold: праг на сходство (по подразбиране 0.75)

    Връща речник:
    {
        'is_correct': bool,     # верен ли е отговорът
        'similarity': float,    # косинусово сходство (0..1)
        'message': str,         # съобщение за потребителя
    }
    """
    # Проверка за празни текстове
    if not student_answer.strip():
        return {
            'is_correct': False,
            'similarity': 0.0,
            'message': 'Не сте въвели отговор.',
        }

    if not correct_answer.strip():
        return {
            'is_correct': False,
            'similarity': 0.0,
            'message': 'Преподавателят не е задал верен отговор.',
        }

    # Изчисляване на семантичното сходство
    similarity = semantic_similarity(student_answer, correct_answer)
    is_correct = similarity >= threshold

    # Формулиране на съобщението
    if is_correct:
        if similarity >= 0.90:
            message = f'Отличен отговор! Сходство: {similarity:.2f}'
        elif similarity >= 0.80:
            message = f'Верен отговор. Сходство: {similarity:.2f}'
        else:
            message = f'Приет отговор (близък до верния). Сходство: {similarity:.2f}'
    else:
        if similarity >= 0.60:
            message = f'Отговорът е частично верен, но не достатъчно точен. Сходство: {similarity:.2f}'
        elif similarity >= 0.40:
            message = f'Отговорът е неточен. Сходство: {similarity:.2f}'
        else:
            message = f'Грешен отговор. Сходство: {similarity:.2f}'

    return {
        'is_correct': is_correct,
        'similarity': similarity,
        'message': message,
    }