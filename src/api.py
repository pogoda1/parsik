import os
import requests
import json
import time
import re
from typing import Dict, Any, Optional, Tuple
from src.config import (
     MODEL_NAME, TIMEOUT, PROMPT_FILE, FEW_SHOT_FILE,
    JSON_SCHEME_FILE, SCHEME_HINTS_FILE, ERROR_CODES, MODEL_NAME_VERY_SMART,
    CATEGORIES_DICT, THEMES_DICT, EVENT_AGE_LIMITS
)
from src.utils import EventValidator
from src.local_model import LocalModel
from src.prompt_manager import PromptManager
from datetime import datetime

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class PromptManager:
    def __init__(self):
        self.prompt = self._load_file(PROMPT_FILE)
        self.json_scheme = self._load_file(JSON_SCHEME_FILE)
        # Remove few_shot examples and scheme_hints to reduce token count
        self.few_shot = self._load_file(FEW_SHOT_FILE)
        self.scheme_hints = self._load_file(SCHEME_HINTS_FILE)

    @staticmethod
    def _load_file(file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def replace_variables(self, text: str, variables: Dict[str, str]) -> str:
        """Replaces variables in text with actual data"""
        for var_name, var_value in variables.items():
            text = text.replace(f"{{{{ {var_name} }}}}", str(var_value))
        return text

    def prepare_prompt(self, message: str) -> str:
        """Prepares the full prompt with all variables"""
        variables = {
            "json_schema": self.json_scheme,
            "schema_hints": self.scheme_hints,
            "few_shot_examples": self.few_shot,
            "message": message
        }
        return self.replace_variables(self.prompt, variables)

class ModelAPI: 
    def __init__(self):
        self.prompt_manager = PromptManager()
        self.model = LocalModel()
        self.stats = {
            'total_events': 0,
            'processing_times': [],
            'very_smart_usage': 0,
            'milestones': {
                '10': {'avg_time': 0, 'smart_usage': 0},
                '50': {'avg_time': 0, 'smart_usage': 0},
                '100': {'avg_time': 0, 'smart_usage': 0}
            }
        }

    def save_stats_to_json(self):
        """Saves current statistics to JSON file"""
        stats_data = {
            'total_events': self.stats['total_events'],
            'current_stats': {
                'avg_processing_time': sum(self.stats['processing_times']) / len(self.stats['processing_times']) if self.stats['processing_times'] else 0,
                'smart_usage_percent': (self.stats['very_smart_usage'] / self.stats['total_events']) * 100 if self.stats['total_events'] > 0 else 0
            },
            'milestones': self.stats['milestones']
        }
        
        with open('data/parser_stats.json', 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, ensure_ascii=False, indent=2)

    def get_stats(self) -> Dict[str, Any]:
        """Returns processing statistics"""
        if not self.stats['processing_times']:
            return {
                'total_events': 0,
                'avg_processing_time': 0,
                'very_smart_usage_percent': 0
            }
            
        avg_time = sum(self.stats['processing_times']) / len(self.stats['processing_times'])
        smart_usage_percent = (self.stats['very_smart_usage'] / self.stats['total_events']) * 100 if self.stats['total_events'] > 0 else 0
        
        # Update milestones if we hit one
        total_events = self.stats['total_events']
        if str(total_events) in self.stats['milestones']:
            self.stats['milestones'][str(total_events)] = {
                'avg_time': avg_time,
                'smart_usage': smart_usage_percent
            }
            self.save_stats_to_json()
            
        return {
            'total_events': total_events,
            'avg_processing_time': avg_time,
            'very_smart_usage_percent': smart_usage_percent
        }

    async def call_model_api(self, text: str) -> Dict[str, Any]:
        """Calls the model API and processes the response"""
        start_time = time.time()
        
        try:
            response = await self._make_api_request(text)
            processing_time = time.time() - start_time
            self.stats['total_events'] += 1
            self.stats['processing_times'].append(processing_time)
            
            # Save stats after each request
            self.save_stats_to_json()
            
            return {
                "result": response,
                "processing_time": processing_time
            }

        except requests.exceptions.Timeout:
            return self._create_error_response(
                f"⏰ Превышено время ожидания ответа от модели ({TIMEOUT} секунд). Попробуйте еще раз.",
                start_time
            )
        except requests.exceptions.ConnectionError:
            return self._create_error_response(
                "🔌 Не удалось подключиться к модели. Проверьте, запущен ли сервер модели.",
                start_time
            )
        except Exception as e:
            return self._create_error_response(
                f"💥 Ошибка при вызове модели: {str(e)}",
                start_time
            )

    async def _make_api_request(self, text: str, isVerySmart: bool = False) -> Dict[str, Any]:
        """Makes the actual API request to the model"""
        if isVerySmart:
            return await self._make_very_smart_request(text)
        return await self._make_regular_request(text)

    def _get_request_data(self, text: str) -> Dict[str, Any]:
        """Prepares request data for API call"""
        return self.prompt_manager.prepare_prompt(text)
    def _get_headers(self) -> Dict[str, str]:
        """Returns common headers for API requests"""
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }


    def _update_event_with_validation(self, dict_event: Dict[str, Any], validate_response: Dict[str, Any]) -> Dict[str, Any]:
        """Updates event data with validation results"""
        for key in validate_response.keys():
            if key not in dict_event and key != "type":
                dict_event[key] = validate_response.get(key, "")
        return dict_event

    async def _make_regular_request(self, text: str) -> Dict[str, Any]:
        """Makes request using regular model"""
        os.makedirs('data', exist_ok=True)
        open('data/regular_request.txt', 'w', encoding='utf-8').write(self._get_request_data(text))
        try:
            response = self.model.generate_structured_response(
                self._get_request_data(text),
                MODEL_NAME
            )
            dict_event = response.get('data', {})
  
            validate_response = self._validate_response(dict_event, text)
            if validate_response.get("type") == "error" or validate_response.get("type") == "error_date_in_past":
                print(dict_event)
                return {
                    'errorCode': ERROR_CODES['NOT_PARSED'] + '_1',
                    'errorDetails': dict_event,
                    'errorText': 'NOT_PARSED'
                }
            if validate_response.get("type") != "success" and 'errorCode' not in dict_event:
                error_data = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
                    "text": text,
                    "dict_event": dict_event,
                    "validate_response": validate_response
                }
                
                # Читаем существующие ошибки или создаем новый список
                try:
                    with open('data/regular_request_error.json', 'r', encoding='utf-8') as f:
                        errors = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    errors = []
                
                if not isinstance(errors, list):
                    errors = []
                    
                # Добавляем новую ошибку
                errors.append(error_data)
                
                # Сохраняем обновленный список ошибок
                with open('data/regular_request_error.json', 'w', encoding='utf-8') as f:
                    json.dump(errors, ensure_ascii=False, indent=2, fp=f)
                print(f"[{get_timestamp()}] ♻️ Модель {MODEL_NAME} не смогла распарсить событие, пытаюсь еще раз с умной моделью {MODEL_NAME_VERY_SMART}")
                return await self._make_very_smart_request(text)

            print(f"[{get_timestamp()}] 🏷️ success: {dict_event.get('eventTitle', '')} model {MODEL_NAME.split('/')[-1]}")
            return self._update_event_with_validation(dict_event, validate_response)
        except Exception as e:
            print(f"[{get_timestamp()}] 💥 Error in _make_regular_request: {str(e)}")
            raise

    async def _make_very_smart_request(self, text: str) -> Dict[str, Any]:
        """Makes request using very smart model"""
        print(f"[{get_timestamp()}] 📡 Making request to very smart model")
        self.stats['very_smart_usage'] += 1

        try:
            response = self.model.generate_structured_response(
                self._get_request_data(text),
                MODEL_NAME_VERY_SMART
            )
            dict_event = response.get('data', {})
            validate_response = self._validate_response(dict_event, text)

            if validate_response.get("type") == "error" or validate_response.get("type") == "error_date_in_past":
                return {
                    'errorCode': ERROR_CODES['NOT_PARSED'] + '_1',
                    'errorDetails': dict_event,
                    'errorText': 'NOT_PARSED'
                }

            print(f"[{get_timestamp()}] 🏷️ success: {dict_event.get('eventTitle', '')} model {MODEL_NAME_VERY_SMART.split('/')[-1]}")
            return self._update_event_with_validation(dict_event, validate_response)
        except Exception as e:
            print(f"[{get_timestamp()}] 💥 Error in _make_very_smart_request: {str(e)}")
            raise

    @staticmethod
    def _validate_response(response, initial_text: str) -> bool:
        try:
            themes = response.get("eventThemes", [])
            categories = response.get("eventCategories", [])
            
            # Log invalid categories
            invalid_categories = [cat for cat in categories if cat not in CATEGORIES_DICT or cat == '']
            if invalid_categories:
                print(f"[{get_timestamp()}] 🏷️ Invalid categories found: {invalid_categories}")
            
            # Log invalid themes
            invalid_themes = [theme for theme in themes if theme not in THEMES_DICT or theme == '']
            if invalid_themes:
                print(f"[{get_timestamp()}] 🎯 Invalid themes found: {invalid_themes}")
            
            # Remove invalid categories
            categories[:] = [cat for cat in categories if cat in CATEGORIES_DICT and cat != '']
            # Remove invalid themes
            themes[:] = [theme for theme in themes if theme in THEMES_DICT and theme != '']
            
            if len(categories) == 0 or len(themes) == 0:
                print(f"[{get_timestamp()}] 🏷️  categories after clean: {categories}")
                print(f"[{get_timestamp()}] 🎯 themes after clean: {themes}")
                return {
                    "type": "error",
                    "eventCategories": categories,
                    "eventThemes": themes,
                    "errorDetails": f"Invalid categories: {invalid_categories} Invalid themes: {invalid_themes}, after valid categories: {categories} and themes: {themes}"
                }
            
            dateFrom = response.get("eventDate", [])[0].get("from")

            # Check if date is in the past
            try:
                # Parse ISO format date and convert to datetime
                date_from = datetime.fromisoformat(dateFrom.replace('Z', '+00:00'))
                current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                if date_from.replace(hour=0, minute=0, second=0, microsecond=0) < current_date:
                    return {
                        "type": "error_date_in_past",
                        "eventCategories": categories,
                        "eventThemes": themes,
                        "errorCode": ERROR_CODES.get('DATE_IN_PAST', 'DATE_IN_PAST'),
                        "errorDetails": f"Event date {dateFrom} is in the past. Current date: {current_date.strftime('%Y-%m-%d')}"
                    }
            except ValueError:
                return {
                    "type": "error",
                    "eventCategories": categories,
                    "eventThemes": themes,
                    "errorCode": ERROR_CODES.get('INVALID_DATE_FORMAT', 'INVALID_DATE_FORMAT'),
                    "errorDetails": f"Invalid date format: {dateFrom}. Expected ISO format (e.g. 2023-01-01T00:00:00.000Z)"
                }

            if response.get("eventTitle") == "":
                return {
                    "type": "error",
                    "eventCategories": categories,
                    "eventThemes": themes
                }
            linkSource = response.get("linkSource")
            if linkSource and linkSource not in initial_text:
                return {
                    "type": "success",
                    'linkSource': ""
                }
            else:
                return {
                    "type": "success",
                    "linkSource": linkSource if 'https://' in linkSource else ''
                }
        
        except Exception as e:
            print(f"[{get_timestamp()}] 💥 validate_response error {e}")
            return {
                    "type": "error",
                    "eventCategories": [],
                    "eventThemes": []
                }


    @staticmethod
    def _create_error_response(error_msg: str, start_time: float) -> Dict[str, Any]:
        """Creates an error response with processing time"""
        return {
            "error": error_msg,
            "processing_time": time.time() - start_time
        } 