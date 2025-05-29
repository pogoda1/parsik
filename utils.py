import json
import os
from difflib import get_close_matches

TEST_JSON_PATH = "SwaggerUIresponse_1.json"
# Новые наборы значений
EVENT_CATEGORIES = tuple(['Концерт', 'Выставка', 'Спектакль', 'Фестиваль', 'Мастер-класс', 
                         'Лекция', 'Кино', 'Турнир', 'Конкурс', 'Праздник'])

EVENT_THEMES = tuple(['Музыка', 'Театр', 'Кино', 'Искусство', 'Спорт', 'Образование', 
                     'Наука', 'Технологии', 'Литература', 'История', 'Природа', 
                     'Путешествия', 'Кулинария', 'Мода', 'Бизнес'])

EVENT_AGE_LIMITS = tuple(['0+', '6+', '12+', '16+', '18+'])

def correct_value(field_name, value):
    """Пытается исправить значение поля на ближайшее допустимое"""
    if field_name == 'eventCategories':
        valid_values = EVENT_CATEGORIES
    elif field_name == 'eventThemes':
        valid_values = EVENT_THEMES
    elif field_name == 'eventAgeLimit':
        valid_values = EVENT_AGE_LIMITS
    else:
        return None, None

    # Сначала проверяем точное совпадение
    if value in valid_values:
        return value, None

    # Пробуем найти ближайшее совпадение
    corrected = get_close_matches(value.lower(), [v.lower() for v in valid_values], n=1, cutoff=0.6)
    if corrected:
        return corrected[0], f"Значение '{value}' исправлено на '{corrected[0]}'"
    
    return None, f"Не удалось найти подходящее значение для '{value}'"

def validate_field(field_name, value):
    """Проверяет значение поля и пытается исправить, если оно недопустимо"""
    if field_name == 'eventCategories' and value not in EVENT_CATEGORIES:
        corrected, message = correct_value(field_name, value)
        if corrected:
            return False, message, corrected
        return False, f"Недопустимое значение категории события: {value}", None
    if field_name == 'eventThemes' and value not in EVENT_THEMES:
        corrected, message = correct_value(field_name, value)
        if corrected:
            return False, message, corrected
        return False, f"Недопустимое значение темы события: {value}", None
    if field_name == 'eventAgeLimit' and value not in EVENT_AGE_LIMITS:
        corrected, message = correct_value(field_name, value)
        if corrected:
            return False, message, corrected
        return False, f"Недопустимое значение возрастного ограничения: {value}", None
    return True, None, None  # Всегда возвращаем 3 значения 

def load_test_data():
    if not os.path.exists(TEST_JSON_PATH):
        return None
    with open(TEST_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_event_by_id(event_id, data):
    return next((item for item in data.get("data", []) if item.get("id") == event_id), None) 