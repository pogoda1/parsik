import requests
import json
import time
import os
from utils import validate_field
import re

API_URL = "http://localhost:1234/v1/chat/completions"
PROMPT_FILE = os.path.expanduser("prompt.md")
FEW_SHOT_FILE = os.path.expanduser("few_shot.md")
JSON_SCHEME_FILE = os.path.expanduser("json_scheme.md")
SCHEME_HINTS_FILE = os.path.expanduser("schema_hints.md")
MODEL_NAME = "deepseek-r1-distill-llama-8b"
# MODEL_NAME = "hermes-3-llama-3.2-3b"

def extract_event_data_from_raw_text(raw_text):
    if '```json' not in raw_text:
        return raw_text
    # Ищем JSON между ```json и ```
    pattern = r"```json\s*(\{.*?\})\s*```"
    match = re.search(pattern, raw_text, re.DOTALL)
    if not match:
        raise ValueError("JSON block not found in the input text")
    
    json_str = match.group(1)
    
    # Парсим JSON
    data = json.loads(json_str)
    event = data.get("data", {})
    
    # Извлекаем поля
    result = {
        "eventTitle": event.get("eventTitle"),
        "eventDescription": event.get("eventDescription"),
        "eventDate": event.get("eventDate", []),
        "eventPrice": event.get("eventPrice", []),
        "eventCategories": event.get("eventCategories", []),
        "eventThemes": event.get("eventThemes", []),
        "eventAgeLimit": event.get("eventAgeLimit"),
        "eventLocation": event.get("eventLocation", {}),
        "linkSource": event.get("linkSource"),
    }
    
    return result



with open(PROMPT_FILE, "r", encoding="utf-8") as f:
    PROMPT = f.read()
with open(FEW_SHOT_FILE, "r", encoding="utf-8") as f:
    FEW_SHOT = f.read()
with open(JSON_SCHEME_FILE, "r", encoding="utf-8") as f:
    JSON_SCHEME = f.read()
with open(SCHEME_HINTS_FILE, "r", encoding="utf-8") as f:
    SCHEME_HINTS = f.read()

def check_for_errors(parsed_json):
    if isinstance(parsed_json, dict) and "errorCode" in parsed_json:
        return parsed_json["errorText"]
    return None

def validate_parsed_data(parsed_json_with_data):
    parsed_json = parsed_json_with_data["data"]
    print("parsed_json",parsed_json)

    """Проверяет все поля в распарсенных данных и пытается исправить недопустимые значения"""
    if not isinstance(parsed_json, dict):
        return "Результат должен быть объектом", None
    
    required_fields = ['eventCategories', 'eventThemes', 'eventAgeLimit']
    corrections = {}
    messages = []
    
    for field in required_fields:
        if field not in parsed_json:
            return f"Отсутствует обязательное поле: {field}", None
        
        is_valid, message, corrected = validate_field(field, parsed_json[field])
        if not is_valid:
            if corrected:
                corrections[field] = corrected
                messages.append(message)
            else:
                return message, None
    
    if corrections:
        # Применяем исправления
        for field, value in corrections.items():
            parsed_json[field] = value
        return None, messages
    
    return None, None

def replace_variables(text, variables):
    """
    Заменяет переменные в тексте на реальные данные
    
    Args:
        text (str): Текст с переменными в формате {{ variable_name }}
        variables (dict): Словарь с переменными и их значениями
        
    Returns:
        str: Текст с замененными переменными
    """
    for var_name, var_value in variables.items():
        text = text.replace(f"{{{{ {var_name} }}}}", str(var_value))
    return text

def call_model_api(text):
    start_time = time.time()
    
    # Создаем словарь с переменными
    variables = {
        "json_schema": JSON_SCHEME,
        "schema_hints": SCHEME_HINTS,
        "few_shot_examples": FEW_SHOT,
        "message": text
    }
    
    full_prompt = replace_variables(PROMPT, variables)
    
    headers = {"Content-Type": "application/json"}
    request_data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are an assistant that extracts structured JSON from unstructured text."},
            {"role": "user", "content": full_prompt}
        ],
        "temperature": 0.7
    }
    
    
    try:
        response = requests.post(API_URL, json=request_data, headers=headers, timeout=120)
        # print("Respon se status:", response.status_code)
        # print("Response text:", response.text)
        response.raise_for_status()
        
        # Проверяем структуру ответа
        res_json = response.json()
        # print("Response JSON structure:", json.dumps(res_json, indent=2))
        
        if "choices" not in res_json:
            raise ValueError("No 'choices' in response")
        if not res_json["choices"]:
            raise ValueError("Empty 'choices' array")
        if "message" not in res_json["choices"][0]:
            raise ValueError("No 'message' in first choice")
        if "content" not in res_json["choices"][0]["message"]:
            raise ValueError("No 'content' in message")
            
        content =  extract_event_data_from_raw_text(res_json["choices"][0]["message"]["content"])
        print("Raw content:", content)
        
        if not content:
            raise ValueError("Empty content from model")
            
        # content = content.replace("```json", "").replace("```", "").strip()
        # print("Cleaned content:", content)
        
        # if not content:
        #     raise ValueError("Empty content after cleaning")
            
        parsed_json = content
        # parsed_json = json.loads(content)
        
        # # Проверяем ошибки в формате ответа
        # err_text = check_for_errors(parsed_json)
        # if err_text:
        #     return {"error": err_text, "processing_time": time.time() - start_time}
        
        # # Проверяем валидность значений полей и пытаемся исправить
        # validation_error, correction_messages = validate_parsed_data(parsed_json)
        # if validation_error:
        #     return {"error": validation_error, "processing_time": time.time() - start_time}
        
        result = {"result": parsed_json, "processing_time": time.time() - start_time}
        # if correction_messages:
        #     result["corrections"] = correction_messages
        
        return result
    except requests.exceptions.Timeout:
        return {"error": "Превышено время ожидания ответа от модели (60 секунд). Попробуйте еще раз.", "processing_time": time.time() - start_time}
    except requests.exceptions.ConnectionError:
        return {"error": "Не удалось подключиться к модели. Проверьте, запущен ли сервер модели.", "processing_time": time.time() - start_time}
    # except json.JSONDecodeError:
    #     return {"error": "Модель вернула некорректный JSON", "processing_time": time.time() - start_time}
    except Exception as e:
        return {"error": f"Ошибка при вызове модели: {str(e)}", "processing_time": time.time() - start_time} 