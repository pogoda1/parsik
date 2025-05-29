import json
import os
from difflib import get_close_matches
from config import (
    EVENT_CATEGORIES, EVENT_THEMES, EVENT_AGE_LIMITS,
    TEST_JSON_PATH
)

class EventValidator:
    @staticmethod
    def correct_value(field_name: str, value: str) -> tuple:
        """Attempts to correct a field value to the nearest valid value"""
        valid_values = {
            'eventCategories': EVENT_CATEGORIES,
            'eventThemes': EVENT_THEMES,
            'eventAgeLimit': EVENT_AGE_LIMITS
        }.get(field_name)

        if not valid_values:
            return None, None

        if value in valid_values:
            return value, None

        corrected = get_close_matches(
            value.lower(),
            [v.lower() for v in valid_values],
            n=1,
            cutoff=0.6
        )
        
        if corrected:
            return corrected[0], f"Значение '{value}' исправлено на '{corrected[0]}'"
        
        return None, f"Не удалось найти подходящее значение для '{value}'"

    @staticmethod
    def validate_field(field_name: str, value: str) -> tuple:
        """Validates a field value and attempts to correct it if invalid"""
        field_validators = {
            'eventAgeLimit': (EVENT_AGE_LIMITS, "возрастного ограничения")
        }

        if field_name not in field_validators:
            return True, None, None

        valid_values, error_msg = field_validators[field_name]
        
        if value not in valid_values:
            corrected, message = EventValidator.correct_value(field_name, value)
            if corrected:
                return False, message, corrected
            return False, f"Недопустимое значение {error_msg}: {value}", None
            
        return True, None, None

class DataLoader:
    @staticmethod
    def load_test_data():
        """Loads test data from JSON file"""
        if not os.path.exists(TEST_JSON_PATH):
            return None
        with open(TEST_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def get_event_by_id(event_id: str, data: dict) -> dict:
        """Retrieves an event by its ID from the data"""
        return next(
            (item for item in data.get("data", []) if item.get("id") == event_id),
            None
        ) 