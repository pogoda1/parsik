import json
import os
from datetime import datetime
from src.config import MODEL_NAME
from src.local_model import LocalModel
from src.prompt_manager import PromptManager


def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_test_data():
    """Загружает тестовые данные из forTest.json"""
    try:
        with open("data/forTest.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[{get_timestamp()}] ❌ Файл data/forTest.json не найден")
        return None
    except json.JSONDecodeError as e:
        print(f"[{get_timestamp()}] ❌ Ошибка парсинга JSON: {e}")
        return None


def load_view_test_data():
    """Загружает существующие результаты тестирования"""
    try:
        with open("data/viewTest.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"models": {}}
    except json.JSONDecodeError:
        return {"models": {}}


def save_view_test_data(data):
    """Сохраняет результаты тестирования в viewTest.json"""
    os.makedirs("data", exist_ok=True)
    with open("data/viewTest.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def test_model():
    """Тестирует модель на данных из forTest.json"""
    print(f"[{get_timestamp()}] 🚀 Начинаю тестирование модели: {MODEL_NAME}")

    # Загружаем тестовые данные
    test_data = load_test_data()
    if not test_data:
        return

    # Загружаем существующие результаты
    view_test_data = load_view_test_data()

    # Инициализируем модель и промпт менеджер
    model = LocalModel()
    prompt_manager = PromptManager()

    # Получаем имя модели для ключа
    model_key = MODEL_NAME.split("/")[-1].replace(".gguf", "")

    # Создаем структуру для результатов этой модели
    model_results = {
        "model_name": MODEL_NAME,
        "tested_at": get_timestamp(),
        "results": [],
    }

    print(
        f"[{get_timestamp()}] 📊 Обрабатываю {len(test_data['data'])} тестовых событий..."
    )

    # Обрабатываем каждое тестовое событие
    for i, event in enumerate(test_data["data"], 1):
        print(
            f"[{get_timestamp()}] 🔄 Обрабатываю событие {i}/{len(test_data['data'])} (ID: {event['id']})"
        )

        try:
            # Подготавливаем промпт
            prompt = prompt_manager.prepare_prompt(event["initialText"])

            # Засекаем время начала обработки
            start_time = datetime.now()
            
            # Получаем ответ от модели
            response = model.generate_structured_response(prompt, MODEL_NAME)
            
            # Вычисляем время обработки
            processing_time = (datetime.now() - start_time).total_seconds()

            # Сохраняем результат
            result = {
                "event_id": event["id"],
                "input_text": event["initialText"],
                "output_json": response,
                "processing_time_seconds": processing_time,
                "processed_at": get_timestamp(),
            }

            model_results["results"].append(result)

            print(f"[{get_timestamp()}] ✅ Событие {event['id']} обработано успешно")

        except Exception as e:
            print(
                f"[{get_timestamp()}] ❌ Ошибка при обработке события {event['id']}: {str(e)}"
            )

            # Сохраняем ошибку
            result = {
                "event_id": event["id"],
                "input_text": event["initialText"],
                "error": str(e),
                "processing_time_seconds": None,
                "processed_at": get_timestamp(),
            }

            model_results["results"].append(result)

    # Обновляем результаты для этой модели (перезаписываем если уже существует)
    view_test_data["models"][model_key] = model_results

    # Сохраняем все результаты
    save_view_test_data(view_test_data)

    print(
        f"[{get_timestamp()}] ✅ Тестирование завершено. Результаты сохранены в data/viewTest.json"
    )
    print(f"[{get_timestamp()}] 📈 Обработано событий: {len(model_results['results'])}")


if __name__ == "__main__":
    test_model()
