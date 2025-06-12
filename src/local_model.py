from datetime import datetime
import json
from typing import List, Dict, Any, Optional
from llama_cpp import Llama
import os
import psutil
import GPUtil
import time
from dateutil import parser
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
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
        # Enhanced system prompts for better context
        self.system_prompts = {
            "event_parser": (
                "Ты эксперт по анализу текстов о мероприятиях. "
                "Твоя задача - точно извлекать структурированную информацию из описаний событий и возвращать её в формате JSON. "
                "Правила:\n"
                "1. Всегда проверяй наличие обязательных полей, особенно даты\n"
                "2. Если дата не указана явно - верни ошибку DATE_NOT_FOUND\n"
                "3. Категории и темы выбирай максимально точно из предложенных вариантов\n"
                "4. Описание должно быть информативным, но лаконичным\n"
                "5. Цены указывай только числами без символов валют\n"
                "6. Адрес должен быть полным и точным"
            )
        }

    def initialize_model(self, model_path: str):
        try:
            self.model = Llama(
                model_path=model_path,
                n_ctx=8192,
                n_gpu_layers=48,
                n_threads=os.cpu_count(),
                n_batch=1024,
                chat_format="chatml",
                verbose=False,
            )
            self.loaded_path = model_path
        except Exception as e:
            print(f"[{get_timestamp()}] 💥 Ошибка при инициализации: {str(e)}")
            raise

    def _adjust_temperature(self, text: str) -> float:
        """Динамически корректирует temperature на основе входного текста"""
        # Более низкая temperature для коротких и четких текстов
        if len(text) < 200:
            return 0.2
        # Средняя temperature для текстов средней длины
        elif len(text) < 500:
            return 0.3
        # Более высокая temperature для длинных и сложных текстов
        return 0.4

    def _adjust_max_tokens(self, text: str) -> int:
        """Динамически корректирует max_tokens на основе входного текста"""
        # Базовое соотношение: примерно 2 токена на каждый символ текста
        base_tokens = len(text) * 2
        
        # Минимальное количество токенов для корректной работы
        min_tokens = 500
        # Максимальное количество токенов для оптимизации производительности
        max_tokens = 2000
        
        # Округляем до ближайшей сотни для читаемости
        adjusted_tokens = round(base_tokens / 100) * 100
        
        # Ограничиваем значение в допустимых пределах
        return max(min_tokens, min(adjusted_tokens, max_tokens))

    def _validate_response(self, response: Dict) -> Optional[Dict]:
        """Проверяет корректность ответа модели"""
        try:
            if "data" not in response:
                return None
                
            required_fields = [
                "eventTitle", "eventDescription", "eventDate",
                "eventPrice", "eventCategories", "eventThemes",
                "eventAgeLimit", "eventLocation", "linkSource"
            ]
            
            for field in required_fields:
                if field not in response["data"]:
                    return None

            # Проверяем и нормализуем даты
            if "eventDate" in response["data"]:
                for date_entry in response["data"]["eventDate"]:
                    try:
                        # Парсим даты и убираем информацию о timezone
                        from_date = parser.parse(date_entry["from"]).replace(tzinfo=None)
                        to_date = parser.parse(date_entry["to"]).replace(tzinfo=None)
                        # Обновляем даты в формате ISO
                        date_entry["from"] = from_date.isoformat()
                        date_entry["to"] = to_date.isoformat()
                    except Exception as e:
                        print(f"[{get_timestamp()}] Ошибка обработки даты: {str(e)}")
                        return None
                    
            return response
        except Exception as e:
            print(f"[{get_timestamp()}] Ошибка валидации: {str(e)}")
            return None

    def generate_structured_response(self, user_prompt: str, model_path: str) -> Dict[str, Any]:
        if not self.model or self.loaded_path != model_path:
            self.initialize_model(model_path)

        # Автоматически подбираем temperature и max_tokens
        temperature = self._adjust_temperature(user_prompt)
        max_tokens = self._adjust_max_tokens(user_prompt)

        retries = 0
        last_error = None

        while retries < self.max_retries:
            try:
                response = self.model.create_chat_completion(
                    messages=[
                        {
                            "role": "system",
                            "content": self.system_prompts["event_parser"]
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
                                                    "excursion", "exhibitions", "well", "lecture",
                                                    "seminar", "conference", "presentation", "webinar",
                                                    "training", "master_class", "vorkshop", "business_game",
                                                    "class", "forum", "mitap", "business_breakfast",
                                                    "meeting", "networking", "mastermind", "theater",
                                                    "movie", "stand__up", "concerts", "party",
                                                    "circus", "festivals", "show", "games",
                                                    "active_rest", "olympics", "battle", "championship",
                                                    "league", "competition", "volunteering", "charity",
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
                                                    "culture_and_art", "science_and_education",
                                                    "industry_specialized", "it_and_the_internet",
                                                    "business_and_entrepreneurship",
                                                    "visual_creativity_visual_graphics",
                                                    "psychology_and_self__knowledge", "humor",
                                                    "music", "travel_and_tourism",
                                                    "cooking_and_gastronomy", "beauty_and_health",
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
                                    "required": [
                                        "eventTitle", "eventDescription", "eventDate",
                                        "eventPrice", "eventCategories", "eventThemes",
                                        "eventAgeLimit", "eventLocation", "linkSource"
                                    ]
                                }
                            },
                            "required": ["data"]
                        }
                    },
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                raw_text = response["choices"][0]["message"]["content"]
                
                # Clean markdown formatting if present
                if raw_text.startswith("```"):
                    raw_text = raw_text.split("\n", 1)[1]
                    raw_text = raw_text.rsplit("\n", 1)[0]
                
                try:
                    parsed = json.loads(raw_text)
                    # Проверяем корректность ответа
                    validated = self._validate_response(parsed)
                    if validated:
                        return validated
                    else:
                        raise ValueError("Invalid response structure")
                        
                except json.JSONDecodeError as e:
                    print(f"[ERROR] Failed to parse JSON: {str(e)}")
                    print(f"[ERROR] Raw text was: {raw_text}")
                    raise

            except Exception as e:
                last_error = e
                retries += 1
                if retries < self.max_retries:
                    print(f"[{get_timestamp()}] Попытка {retries}/{self.max_retries}. Ошибка: {str(e)}")
                    time.sleep(self.retry_delay * retries)  # Увеличиваем задержку с каждой попыткой
                continue
            
        print(f"[{get_timestamp()}] 💥 Все попытки исчерпаны. Последняя ошибка: {str(last_error)}")
        raise last_error

textAds = "Из Калининграда организуют регулярные экскурсии в национальный парк «Куршская коса». Участники посетят ключевые локации заповедника, услышат, как «поёт» песок, пообедают в трактире, а в завершение дня посетят сыроварню и прогуляются по Зеленоградску. \n\n👉 забронировать экскурсию (https://dvuhmetrovigid.ru/excursions/?did=0039&utm_source=part&utm_medium=0039&excursion=233)\n\nЦена с плотным обедом 3900 ₽, длительность 8 часов.\n\nПодписаться на АНОНС39 (https://t.me/+-cCRoVroPdZiMDYy)"
textEvent = "Название: Екатерина Яшникова в Калининграде. Дата: 27 июля (воскресенье) 20:00 – 22:30. Описание: Екатерина Яшникова – девушка с гитарой и огромными амбициями. Понятные истории и блестяще адаптированный для поп-рока русский язык делают каждую песню притягательной.\n\nОна создает себя сама — и у нее это получается. Миллионы просмотров на YouTube, концерты по всей стране, мощные коллаборации, в том числе с группой Uma2rman, ставшие народными песнями — это только часть побед за девятилетнюю историю проекта.\n\nОна поет на «Квартирнике у Маргулиса» и «Дикой Мяте», YLETAЙ и STEREOLETO и один за другим покоряет рок-фестивали и снимает клипы, которые выигрывают награды на конкурсе короткометражек. В ее дискографии – 5 EP, 7 полноценных альбомов и большое количество синглов, в которых много любви. Потому что без любви — к миру и слушателю — невозможно творить, как Екатерина Яшникова: ярко, живо, остро и предельно честно, создавая не просто песни — целые миры, в которых каждый находит себя.\n\nВнимание: нумерация и расположение мест за столами являются условными, имеет значение только номер стола. Цена: 1200. Адрес: ул. Дзержинского, 31В, Калининград. Категория: концерт"
textEvent2 = "Название: ELECTRODVOR x Ш presents. Дата: 13 (пятница) 23:22 – 14 (суббота) 06:00 июня. Описание: ELECTRODVOR x Ш presents:\n\nUTOPIA: CHAPTER ONE\nsluts, zombies, vampires, dolls, plants\n\n локация: electrodvor\n дата: пятница, 13 июня\n хосты: Ш\n\nв эту ночь всё скрытое — всплывёт.\nвсё мёртвое — задвигается в ритме.\nа все «не такие» — станут собой.\n\nзомби целуются с растениями,\nкуклы режут воздух,\nslutty tatty ведут в утопию…\nили прямо в ад. who knows?\n\n лекция об истории рейва\n мистический опыт и напитки\n музыкальный стол от декадентов и декаденток городка К:\nHard girls crew (Naya, YASYA, Xenia Raketa) Ah_Ulya, Selectica, daria ave_sna, przrk, dj voroffka, nrthwst, givemeyourtop & ownernaservere\nтранслируют:\nHard style,\nArtist open mind selection,\nTropical bass,\nGothic rave\nDarkwave\nWitch House \nIndustrial / EBM  & live performances\n\n 13 июня — ночь, чтобы сиять.\nпокажи миру свой аутфит и выиграй приз.\n\nглава первая скоро откроется.\nне пропусти портал:\nподписывайся, следи, входи.\n\n early bird — в продаже\n\n#utopia_party #chapterone #slutszombiesvampires #undergroundmagic. Цена: 666. Адрес: Каштановая аллея 1 «а», Калининград. Категория: рейв"
textEvent3 = "Название: Легенды ВИА 70-80-90х «МЫ ИЗ СССР». Юбилейный концерт. 10 лет поём для вас. Дата: 14 сентября (воскресенье) 15:00. Возрастное ограничение: 12. Цена: от 3000 до 14500. Адрес: Калининградская область, Светлогорск, улица Ленина, 11. Описание: 14 сентября в Светлогорске на берегу Балтийского моря пройдет большой юбилейный десятый гала-концерт «Легенды ВИА 70-80-90х «МЫ ИЗ СССР».&nbsp;В программе прозвучат самые популярные хиты 70-80-90х.\n\nПо словам музыкальных критиков концерт «МЫ СССР» входит в ТОП лучших концертов Калининграда! И лучшие из лучших работают с нами!\n\nВ основном составе концертной программы принимают участие артисты: Валерий Ярушин, Александр Акинин, Василий Курсаков, Александр Диксон, Сергей Бойко, Анатолий Ярмоленко&nbsp;– солисты, экс-солисты, музыканты легендарных вокально-инструментальных ансамблей (ВИА):\n«АРИЭЛЬ»,\n«ЛЕЙСЯ, ПЕСНЯ»\n«КРАСНЫЕ МАКИ»\n«ГОЛУБЫЕ ГИТАРЫ»\n«КАРНАВАЛ»\n«ШЕСТЕРО МОЛОДЫХ»\n«БЕЛЫЙ ОРЁЛ»\n«СЯБРЫ»\n«ПЕСНЯРЫ»\n\n«ВЕСЁЛЫЕ РЕБЯТА» –&nbsp;Гость программы Леонид Адольфович Бергер приедет к нам на концерт из Австралии, эксклюзивно для города Калининград\nЮРИЙ ЛОЗА («Свитый из песен и слов…», «Плот», «Сто часов», «Пой, моя гитара, пой»)\nВЛАДИМИР МАРКИН («Сиреневый туман», «Я готов целовать песок», «Белая черемуха», «Что зазвонят опять Колокола и ты войдешь в распахнутые двери»)\n«ФРИСТАЙЛ» СЕРГЕЙ ДУБРОВИН («Ах, какая женщина!»)\nМИХАИЛ ДОЛОТОВ/АНАТОЛИЙ КАШЕПАРОВ («Беловежская пуща», «Наши любимые», «Вологда», «Алеся»)\nАЛЕКСАНДР СОЛОДУХА («Здравствуй чужая милая, та что была моей»)\n\nВ программе не исключены и сюрпризы, ведь мало ли кто зайдёт на наш огонёк!\n\nО концерте:\nВесёлые заводные ребята советского времени с огнём в глазах ждут вас 14 сентября на самой культовой площадке Калининграда в «Театре эстрады «Янтарь Холл»!\n\nТворческий коллектив и программа были созданы в 2004 году. Первые концерты прошли в Австралии в городах Мельбурне и Сиднее, которые произвели фурор среди бывших эмигрантов из СССР. В настоящее время коллектив «Легенды ВИА 70-80-90х» успешно, с аншлагами гастролирует по необъятным просторам бывшего СССР и зарубежья.\n\n50 лет назад вся страна слушала Вокально-Инструментальные Ансамбли. Именно они исполняли песни, ставшие хитами вне времени, вошедшие в золотой фонд популярной музыки:\n«Люди встречаются», «Напиши мне письмо», «В краю магнолий, «Алеся», «Беловежская пуща», «Лягу-прилягу», «Как прекрасен этот мир», «Лишь позавчера нас судьба свела», «Для меня нет тебя прекраснее, «Вологда», «Как упоительны в … вечера», Глухариная зор, Вы шумите, березы, \"Гулять так гулять!\", «Алешкина любовь», \"Белоруссия\", «Кто тебе сказал?», «Ах, какая женщина», «Там где клён шумит», «Поверь в мечту», Бухгалтер, «Каскадеры», «Аэропорт», «Трава у дома», «Горько», «Я буду долго гнать велосипед», «Розовые розы Светке Соколовой», «Ты мне не снишься», «Моя любовь жива», «Так вот какая ты», «Потому что нельзя быть на свете красивой такой», «Бродячие артисты», «До чего ж я не везучий», «Листья закружат», «Спасательный круг», Мой адрес – Советский Союз, и многие другие песни, вызывая теплые ностальгические чувства воспоминания о нашей юности, первой любви, и о той огромной стране, где все мы были единым народом государства – СССР.\n\nТолько стоит заиграть&nbsp;«Люди встречаются, люди влюбляются женятся...», «Мечты сбываются...», «Я вспоминаю, тебя вспоминаю...», и зал с первой же ноты поет песни в унисон.\nВ этом уникальное ретро-шоу прозвучат и эти песни, и многие другие, по-прежнему любимые публикой. Прозвучат не с «чужого голоса», а в том же самом исполнении, в котором когда-то запали в сердце каждого жителя необъятного СССР.\n\nЛюди всегда проявляли бурный интерес к необычным проектам.\nИ концерт «МЫ ИЗ СССР» – это волнующее путешествие по славным временам чей-то молодости! Мы гарантирует вам в этот вечер 100% радости и позитива!!! Будет очень душевно и весело!\n\nПродолжительность концерта 1 час 45 мин без антракта.\n\n*В СОСТАВЕ АРТИСТОВ ВОЗМОЖНЫ ИЗМЕНЕНИЯ БЕЗ ПРЕДВАРИТЕЛЬНОГО УВЕДОМЛЕНИЯ!. Категории: Концерты"
if __name__ == "__main__":
    model = LocalModel()
    promptManager = PromptManager()
    
    text1 = promptManager.prepare_prompt(textEvent)
    text2 = promptManager.prepare_prompt(textAds)
    text3 = promptManager.prepare_prompt(textEvent2)
    text4 = promptManager.prepare_prompt(textEvent3)
    
    
    forPrint = [
        text4,text4,text4,
        text2,text2,text2,
        text1,text1,text1,
        text3,text3,text3,

        ]

    for i in forPrint:
        res = model.generate_structured_response(i, MODEL_NAME)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    

