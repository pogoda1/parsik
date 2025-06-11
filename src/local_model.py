from datetime import datetime
import json
from typing import List, Dict, Any
from llama_cpp import Llama
import os
import psutil
import GPUtil
from src.config import MODEL_NAME
from src.prompt_manager import PromptManager

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def check_system_info():
    info = []
    info.append(f"CPU использование: {psutil.cpu_percent()}%")
    try:
        gpus = GPUtil.getGPUs()
        for gpu in gpus:
            info.append(f"GPU {gpu.name}:")
            info.append(f"- Загрузка GPU: {gpu.load*100:.1f}%")
            info.append(f"- Память GPU: {gpu.memoryUsed}MB / {gpu.memoryTotal}MB")
    except:
        info.append("Не удалось получить информацию о GPU")
    return "\n".join(info)


class LocalModel:
    def __init__(self):
        self.model = None
        self.loaded_path = None

    def initialize_model(self, model_path: str):
        try:
            self.model = Llama(
                model_path=model_path,
                n_ctx=8192,
                n_gpu_layers=48,
                n_threads=os.cpu_count(),
                n_batch=1024,
                chat_format="chatml",  # ВАЖНО для structured output
                verbose=False,
            )
            self.loaded_path = model_path
        except Exception as e:
            print(f"[{get_timestamp()}] 💥 Ошибка при инициализации: {str(e)}")
            raise

    def generate_structured_response(self, user_prompt: str, model_path: str, temperature: float = 0.3) -> Dict[str, Any]:
        if not self.model or self.loaded_path != model_path:
            self.initialize_model(model_path)


        try:
            response = self.model.create_chat_completion(
                messages=[
                     {
                    "role": "system",
                    "content": (
                        "Ты помощник, который возвращает СТРОГО JSON. "
                        "Если пользовательский текст содержит описание реального мероприятия — сгенерируй структуру. "
                        "Если даты явно не указана в тексте мероприятия — верни ошибку в формате {\"errorCode\": 2, \"errorText\": \"DATE_NOT_FOUND\"}. "
                    )
                },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                response_format={
                    "type": "json_object",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "data": {
                                "type": "object",
                                "properties": {
                                    "eventTitle": {"type": "string"},
                                    "eventDescription": {"type": "string"},
                                    "eventDate": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "from": {"type": "string"},
                                                "to": {"type": "string"},
                                            },
                                            "required": ["from", "to"]
                                        }
                                    },
                                    "eventPrice": {
                                        "type": "array",
                                        "items": {"type": "number"}
                                    },
                                    "eventCategories": {
                                        "type": "array",
                                        "items": {
                                            "type": "string",
                                            "enum": [
                                                "excursion",
                                                "exhibitions",
                                                "well",
                                                "lecture",
                                                "seminar",
                                                "conference",
                                                "presentation",
                                                "webinar",
                                                "training",
                                                "master_class",
                                                "vorkshop",
                                                "business_game",
                                                "class",
                                                "forum",
                                                "mitap",
                                                "business_breakfast",
                                                "meeting",
                                                "networking",
                                                "mastermind",
                                                "theater",
                                                "movie",
                                                "stand__up",
                                                "concerts",
                                                "party",
                                                "circus",
                                                "festivals",
                                                "show",
                                                "games",
                                                "active_rest",
                                                "olympics",
                                                "battle",
                                                "championship",
                                                "league",
                                                "competition",
                                                "volunteering",
                                                "charity",
                                                "social_initiatives"
                                            ]
                                        },
                                        "minItems": 1
                                    },
                                    "eventThemes": {
                                        "type": "array",
                                        "items": {
                                            "type": "string",
                                            "enum": [
                                                "culture_and_art",
                                                "science_and_education",
                                                "industry_specialized",
                                                "it_and_the_internet",
                                                "business_and_entrepreneurship",
                                                "visual_creativity_visual_graphics",
                                                "psychology_and_self__knowledge",
                                                "humor",
                                                "music",
                                                "travel_and_tourism",
                                                "cooking_and_gastronomy",
                                                "beauty_and_health",
                                                "sport"
                                            ]
                                        },
                                        "minItems": 1
                                    },  
                                    "eventAgeLimit": {"type": "string"},
                                    "eventLocation": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "address": {"type": "string"}
                                        },
                                        "required": ["name", "address"]
                                    },
                                    "linkSource": {"type": "string"}
                                },
                                "required": ["eventTitle", "eventDescription", "eventDate", "eventPrice",
                                             "eventCategories", "eventThemes", "eventAgeLimit",
                                             "eventLocation", "linkSource"]
                            }
                        },
                        "required": ["data"]
                    }
                },
                temperature=temperature,
                max_tokens=800
            )

            raw_text = response["choices"][0]["message"]["content"]
            
            # Clean markdown formatting if present
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1]  # Remove first line with ```json
                raw_text = raw_text.rsplit("\n", 1)[0]  # Remove last line with ```
            
            try:
                parsed = json.loads(raw_text)
                return parsed
            except json.JSONDecodeError as e:
                print(f"[ERROR] Failed to parse JSON: {str(e)}")
                print(f"[ERROR] Raw text was: {raw_text}")
                raise

        except Exception as e:
            print(f"[{get_timestamp()}] 💥 Ошибка генерации JSON: {str(e)}")
            raise

textAds = "Из Калининграда организуют регулярные экскурсии в национальный парк «Куршская коса». Участники посетят ключевые локации заповедника, услышат, как «поёт» песок, пообедают в трактире, а в завершение дня посетят сыроварню и прогуляются по Зеленоградску. \n\n👉 забронировать экскурсию (https://dvuhmetrovigid.ru/excursions/?did=0039&utm_source=part&utm_medium=0039&excursion=233)\n\nЦена с плотным обедом 3900 ₽, длительность 8 часов.\n\nПодписаться на АНОНС39 (https://t.me/+-cCRoVroPdZiMDYy)"
textEvent = "Название: Екатерина Яшникова в Калининграде. Дата: 27 июля (воскресенье) 20:00 – 22:30. Описание: Екатерина Яшникова – девушка с гитарой и огромными амбициями. Понятные истории и блестяще адаптированный для поп-рока русский язык делают каждую песню притягательной.\n\nОна создает себя сама — и у нее это получается. Миллионы просмотров на YouTube, концерты по всей стране, мощные коллаборации, в том числе с группой Uma2rman, ставшие народными песнями — это только часть побед за девятилетнюю историю проекта.\n\nОна поет на «Квартирнике у Маргулиса» и «Дикой Мяте», YLETAЙ и STEREOLETO и один за другим покоряет рок-фестивали и снимает клипы, которые выигрывают награды на конкурсе короткометражек. В ее дискографии – 5 EP, 7 полноценных альбомов и большое количество синглов, в которых много любви. Потому что без любви — к миру и слушателю — невозможно творить, как Екатерина Яшникова: ярко, живо, остро и предельно честно, создавая не просто песни — целые миры, в которых каждый находит себя.\n\nВнимание: нумерация и расположение мест за столами являются условными, имеет значение только номер стола. Цена: 1200. Адрес: ул. Дзержинского, 31В, Калининград. Категория: концерт"

if __name__ == "__main__":
    model = LocalModel()
    promptManager = PromptManager()
    
    text1 = promptManager.prepare_prompt(textEvent)
    text2 = promptManager.prepare_prompt(textAds)

    
    
    forPrint = [
        text2,
text2,
text2,
text2,
text2,
text2,
text1,
text1,
text1,
text1,
text1,
text1,
text1,
text1,

        ]

    for i in forPrint:
        res = model.generate_structured_response(i, MODEL_NAME)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    

