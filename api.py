import requests
import json
import time
import os
from utils import validate_field

API_URL = "http://localhost:1234/v1/chat/completions"
PROMPT_FILE = os.path.expanduser("prompt.md")

with open(PROMPT_FILE, "r", encoding="utf-8") as f:
    PROMPT = f.read()

def check_for_errors(parsed_json):
    if isinstance(parsed_json, dict) and "errorCode" in parsed_json:
        return parsed_json["errorText"]
    return None

def validate_parsed_data(parsed_json):
    """Проверяет все поля в распарсенных данных"""
    if not isinstance(parsed_json, dict):
        return "Результат должен быть объектом"
    
    required_fields = ['department', 'operation', 'crop']
    for field in required_fields:
        if field not in parsed_json:
            return f"Отсутствует обязательное поле: {field}"
        
        is_valid, error_msg = validate_field(field, parsed_json[field])
        if not is_valid:
            return error_msg
    
    return None

def call_model_api(text):
    start_time = time.time()
    full_prompt = f"{PROMPT}\n\n{text}"
    headers = {"Content-Type": "application/json"}
    request_data = {
        "model": "gemma-3-4b-it-qat",
        "messages": [
            {"role": "system", "content": "You are an assistant that extracts structured JSON from unstructured text."},
            {"role": "user", "content": full_prompt}
        ],
        "temperature": 0.0
    }
    try:
        response = requests.post(API_URL, json=request_data, headers=headers, timeout=60)
        response.raise_for_status()
        res_json = response.json()
        content = res_json["choices"][0]["message"]["content"]
        content = content.replace("```json", "").replace("```", "").strip()
        parsed_json = json.loads(content)
        
        # Проверяем ошибки в формате ответа
        err_text = check_for_errors(parsed_json)
        if err_text:
            return {"error": err_text, "processing_time": time.time() - start_time}
        
        # Проверяем валидность значений полей
        validation_error = validate_parsed_data(parsed_json)
        if validation_error:
            return {"error": validation_error, "processing_time": time.time() - start_time}
        
        return {"result": parsed_json, "processing_time": time.time() - start_time}
    except requests.exceptions.Timeout:
        return {"error": "Превышено время ожидания ответа от модели (60 секунд). Попробуйте еще раз.", "processing_time": time.time() - start_time}
    except requests.exceptions.ConnectionError:
        return {"error": "Не удалось подключиться к модели. Проверьте, запущен ли сервер модели.", "processing_time": time.time() - start_time}
    except json.JSONDecodeError:
        return {"error": "Модель вернула некорректный JSON", "processing_time": time.time() - start_time}
    except Exception as e:
        return {"error": f"Ошибка при вызове модели: {str(e)}", "processing_time": time.time() - start_time} 