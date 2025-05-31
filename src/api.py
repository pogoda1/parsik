import requests
import json
import time
import re
from typing import Dict, Any, Optional, Tuple
from src.config import (
    API_URL, MODEL_NAME, TIMEOUT, PROMPT_FILE, FEW_SHOT_FILE,
    JSON_SCHEME_FILE, SCHEME_HINTS_FILE, ERROR_CODES, MODEL_NAME_VERY_SMART,
    CATEGORIES_DICT, THEMES_DICT
)
from src.utils import EventValidator
import aiohttp
from datetime import datetime

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class PromptManager:
    def __init__(self):
        self.prompt = self._load_file(PROMPT_FILE)
        self.few_shot = self._load_file(FEW_SHOT_FILE)
        self.json_scheme = self._load_file(JSON_SCHEME_FILE)
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

class EventExtractor:
    @staticmethod
    def extract_event_data_from_raw_text(raw_text: str, initial_text: Optional[str] = None) -> Dict[str, Any]:
        """Extracts event data from raw text response"""
        print(f"[{get_timestamp()}] 🔍 Starting event data extraction")

        pattern = r"```json\s*(\{.*?\})\s*```"
        matches = list(re.finditer(pattern, raw_text, re.DOTALL))
        
        if not matches:
            return json.loads(raw_text).get("data", {})
        json_str = matches[-1].group(1)

        try:
            data = json.loads(json_str)
            event = data.get("data", {})
            textError = data.get("errorText", "")
            
            if textError == 'ADS':
                return data
                
            event_dates = event.get("eventDate", [])
            if not event_dates:
                print(f"[{get_timestamp()}] 🏷️ event: {event}")
                return {
                    "errorCode": ERROR_CODES['DATE_NOT_FOUND'] + '_3',
                    "errorDetails": event,
                    "errorText": "DATE_NOT_FOUND"
                }
            
            date_from_first_day = event_dates[0].get("from")
            
            if not date_from_first_day or not isinstance(date_from_first_day, str):
                return {
                    "errorCode": ERROR_CODES['INVALID_DATE'] + '_4',
                    "errorDetails": json.dumps(event, ensure_ascii=False, indent=2),
                    "errorText": "DATE_NOT_FOUND"
                }
            
            return event
        except Exception as e:
            raise ValueError(f"Error extracting event data: {str(e)}")

class ModelAPI: 
    def __init__(self):
        print(f"[{get_timestamp()}] 🧠 Initializing ModelAPI")
        self.prompt_manager = PromptManager()
        self.event_extractor = EventExtractor()

    async def call_model_api(self, text: str) -> Dict[str, Any]:
        """Calls the model API and processes the response"""
        start_time = time.time()
        print(f"[{get_timestamp()}] 🤖 Starting AI model call")
        
        try:
            response = await self._make_api_request(text)
            print(f"[{get_timestamp()}] ✅ AI model call completed in {time.time() - start_time:.2f} seconds")
            return {
                "result": response,
                "processing_time": time.time() - start_time
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
        print(f"[{get_timestamp()}] 📡 Making API request to model")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }
        current_model = MODEL_NAME_VERY_SMART if isVerySmart else MODEL_NAME
        
        request_data = {
            "model": current_model,
            "messages": [
                {"role": "system", "content": "You are an assistant that extracts structured JSON from unstructured text."},
                {"role": "user", "content": self.prompt_manager.prepare_prompt(text)}
            ],
            "temperature": 0.7
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=request_data, headers=headers, timeout=TIMEOUT) as response:
                response.raise_for_status()
                res_json = await response.json()
                dict_event = EventExtractor.extract_event_data_from_raw_text(res_json["choices"][0]["message"]["content"])

                validate_response = self._validate_response(dict_event, text)
                if validate_response.get("type") != "success" and 'errorCode' not in dict_event:
                    print(f"[{get_timestamp()}] ♻️ Модель {current_model} не смогла распарсить событие, пытаюсь еще раз с умной моделью {MODEL_NAME_VERY_SMART}")
                    responseVerySmart = await self._make_api_request(text, True)
                    print(f"[{get_timestamp()}] 🏷️ have answer from responseVerySmart")
                    return responseVerySmart

                print(f"[{get_timestamp()}] 🏷️ success: {dict_event.get('eventTitle', '')} model {current_model}")
                for key in validate_response.keys():
                    if key not in dict_event:
                        if key == "type":
                            continue
                        dict_event[key] = validate_response.get(key, "")

                return dict_event

    @staticmethod
    def _validate_response(response, initial_text: str) -> bool:
        """Validates the response structure"""
        try:
            print(f"[{get_timestamp()}] 🔍 Starting response validation")
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
                    "eventThemes": themes
                }
            
            if response.get("eventAgeLimit") == "":
                return {
                    "type": "success",
                    "eventAgeLimit": '12',
                }
            if response.get("eventTitle") == "":
                return {
                    "type": "error",
                    "eventCategories": categories,
                    "eventThemes": themes
                }
            linkSource = response.get("linkSource")
            if linkSource and linkSource not in initial_text:
                if 'https://' not in linkSource:
                    return {
                    "type": "error",
                    'linkSource': ''
                    }
                else:
                    return {
                        "type": "error",
                        'linkSource': linkSource
                    }
                
            return {
                "type": "success",
                "eventCategories": categories,
                "eventThemes": themes
            }
        except Exception as e:
            print(f"[{get_timestamp()}] 💥 validate_response error {e}")
            return     {
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