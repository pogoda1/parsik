import asyncio
import json
import requests
import os
from time import sleep
from src.api import ModelAPI
from src.config import ACCESS_TOKEN
from datetime import datetime

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

async def getListForSync():
    try:
        print(f"[{get_timestamp()}] 🔄 Starting to fetch list for sync")
        response = requests.post(
            'https://test-back.momenta.place/backend/integration/parsing/admin/getAllEventsForParsing',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            }
        )
        response.raise_for_status()  # Проверка на ошибки
        return response.json()['data']['data']
    except requests.exceptions.RequestException as e:
        print(f"[{get_timestamp()}] 🌐 Error making request: {e}")
        return None


def clearLocalList():
    with open('data/notParserList.json', 'w', encoding='utf-8') as file:
        json.dump({"data": []}, file, ensure_ascii=False, indent=4)

def deleteFromLocalList(id):
    with open('data/notParserList.json', 'r', encoding='utf-8') as file:
        existing_data = json.load(file)
    existing_data['data'] = [item for item in existing_data['data'] if item['id'] != id]
    with open('data/notParserList.json', 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)
    return


async def parseEventsFromLocalList():
    with open('data/notParserList.json', 'r', encoding='utf-8') as file:
        existing_data = json.load(file)
    # [:1] берет только первый элемент из списка data
    for event in existing_data['data'][:5]:
        print(f"[{get_timestamp()}] 🤖 Starting AI processing for event {event['id']}")
        await parseEvent(event)
        sleep(10)
    if len(existing_data['data']) == 0:
        print(f"[{get_timestamp()}] 🔄 Нет элементов для обработки")
        return
    else:
        await parseEventsFromLocalList()

async def parseEvent(event):
    try:
        print(f"[{get_timestamp()}] 🧠 Initializing AI model for event {event['id']}")
        model_api = ModelAPI()
        response = await model_api.call_model_api(event['input'])
        result = json.dumps(response.get('result', {}), ensure_ascii=False, indent=2)
        payload = {
            "id": event['id'],
            "result": json.loads(result)
        }
        print(f"[{get_timestamp()}] 📤 Sending processed event {event['id']} to server")
        request = requests.post(
            'https://test-back.momenta.place/backend/integration/parsing/fillParsingEventResult',
            headers={
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            },
            json=payload
        )
        fillModelLocalList({**payload, "responseFromServer": request.json(), "initial_event": event['input'], "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        deleteFromLocalList(event['id'])
        
        result_dict = response.get('result', {})
        if isinstance(result_dict, dict) and result_dict.get('errorCode', 0) == 1:
            print(f"[{get_timestamp()}] 🚫 Обработал элемент - {event['id']} {result_dict.get('errorText', '')}")
        else:
            print(f"[{get_timestamp()}] ✅ Обработал элемент - {event['id']}")
    except Exception as e:
        print(f"[{get_timestamp()}] 💥 Error processing event {event['id']}: {e}")
        # Удаляем проблемный элемент из списка чтобы не зациклиться
        deleteFromLocalList(event['id'])



def fillLocalList(list):    
    if not list:
        print(f"[{get_timestamp()}] 📭 No data received from API")
        return
        
    clearLocalList()
    # Сначала читаем существующие данные
    existing_data = {"data": []}
    if os.path.exists('data/notParserList.json'):
        try:
            with open('data/notParserList.json', 'r', encoding='utf-8') as file:
                existing_data = json.load(file)
        except json.JSONDecodeError:
            pass
    
    # Добавляем новые данные
    if list:
        existing_data["data"].extend(list)
    
    # Записываем обновленные данные
    with open('data/notParserList.json', 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)


def fillModelLocalList(payload):
    if not payload:
        print(f"[{get_timestamp()}] 📭 No data received from API")
        return
    result = json.dumps(payload, ensure_ascii=False, indent=2)  # result will be str, not dict since json.dumps returns string
   
    # Сначала читаем существующие данные
    existing_data = {"data": []}
    if os.path.exists('data/parserList.json'):
        try:
            with open('data/parserList.json', 'r', encoding='utf-8') as file:
                existing_data = json.load(file)
        except json.JSONDecodeError:
            pass

    # Добавляем payload как элемент списка
    existing_data["data"].append(payload)

    # Записываем обновленные данные
    with open('data/parserList.json', 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)



async def sync():
    try:
        print(f"[{get_timestamp()}] 🚀 Starting sync process")
        # Создаем директорию если её нет
        os.makedirs('data', exist_ok=True)
        
        # list = await getListForSync()
        # print(f"[{get_timestamp()}] 🔄 Получил список из {len(list)} элементов")
        # fillLocalList(list)
        await parseEventsFromLocalList()
            
    except Exception as e:
        print(f"[{get_timestamp()}] 💥 Error loading config: {e}")
        await parseEventsFromLocalList()

if __name__ == "__main__":
    print(f"[{get_timestamp()}] 🚀 Starting application")
    asyncio.run(sync())

