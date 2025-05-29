import asyncio
import json
import requests
import os
from src.api import ModelAPI
with open('config.json', 'r', encoding='utf-8') as file:
            config = json.load(file)

accessToken = config.get("accessToken")

async def getListForSync():
    try:
        response = requests.post(
            'https://test-back.momenta.place/backend/integration/parsing/getEventsForParsing',
            headers={
                'Authorization': f'Bearer {accessToken}',
                'Content-Type': 'application/json'
            }
        )
        print('LOG: Получил данные с сервера: количество элементов - ', len(response.json()['data']))
        response.raise_for_status()  # Проверка на ошибки
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None


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
    for event in existing_data['data']:
        parseEvent(event)        

def parseEvent(event):
    model_api = ModelAPI()
    response =  model_api.call_model_api(event['input'])
    result = json.dumps(response["result"], ensure_ascii=False)  # result will be str, not dict since json.dumps returns string
    payload = {
        "id": event['id'],
        "result": json.loads(result)
    }
    request = requests.post(
        'https://test-back.momenta.place/backend/integration/parsing/fillParsingEventResult',
        headers={
            'Authorization': f'Bearer {accessToken}',
            'Content-Type': 'application/json'
        },
        json=payload
    )
    fillModelLocalList({**payload, "responseFromServer": request.json(), "initial_event": event['input']})
    deleteFromLocalList(event['id'])
    if response['result']['errorCode'] == 1:
        print('LOG: Обработал элемент ❌ - ', event['id'])
    else:
        print('LOG: Обработал элемент ✅ - ', event['id'])



def fillLocalList(list):    
    if not list or 'data' not in list or not list['data']:
        print("No data received from API")
        return
        
    
    # Сначала читаем существующие данные
    existing_data = {"data": []}
    if os.path.exists('data/notParserList.json'):
        try:
            with open('data/notParserList.json', 'r', encoding='utf-8') as file:
                existing_data = json.load(file)
        except json.JSONDecodeError:
            pass
    
    # Добавляем новые данные
    if list and "data" in list:
        existing_data["data"].extend(list["data"])
    
    # Записываем обновленные данные
    with open('data/notParserList.json', 'w', encoding='utf-8') as file:
        json.dump(existing_data, file, ensure_ascii=False, indent=4)


def fillModelLocalList(payload):
    if not payload:
        print("No data received from API")
        return
    result = json.dumps(payload, ensure_ascii=False)  # result will be str, not dict since json.dumps returns string
   
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
        # Создаем директорию если её нет
        os.makedirs('data', exist_ok=True)
        
        
        list = await getListForSync()
        fillLocalList(list)
        await parseEventsFromLocalList()
            
    except Exception as e:
        print(f"Error loading config: {e}")

if __name__ == "__main__":
    asyncio.run(sync())

