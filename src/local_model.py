from datetime import datetime
import json
from typing import List, Dict, Any
from llama_cpp import Llama
import os
import psutil
import GPUtil
import threading
import time

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def check_system_info():
    info = []
    info.append(f"CPU использование: {psutil.cpu_percent()}%")
    try:
        gpus = GPUtil.getGPUs()
        for gpu in gpus:
            info.append(f"GPU {gpu.name}:")
            info.append(f"- Загрузка GPU: {gpu.load*100}%")
            info.append(f"- Память GPU: {gpu.memoryUsed}MB / {gpu.memoryTotal}MB")
    except:
        info.append("Не удалось получить информацию о GPU")
    return "\n".join(info)

class LocalModel:
    def __init__(self):
        self.model = None
        
    def initialize_model(self, model_path: str):
        try:
            self.model = Llama(
                model_path=model_path,
                n_ctx=16384,
                n_gpu_layers=35,
                n_threads=os.cpu_count(),
                n_batch=4096,  # Увеличено для длинных последовательностей
                verbose=False,  # Включите для отладки
                echo=False
            )
        except Exception as e:
            print(f"[{get_timestamp()}] 💥 Error initializing model: {str(e)}")
            raise

    def generate_response(self, prompt: str, model_path: str, temperature: float = 0.8) -> str:
        print(f"[{get_timestamp()}] 📡 generate model: {model_path.split('/')[-1]}")
        if not self.model or self.model.model_path != model_path:
            self.initialize_model(model_path)
            
        try:
            output = self.model(
                prompt,
                temperature=temperature,
                max_tokens=16384  # Увеличьте для полного ответа
            )
            response = output["choices"][0]["text"].strip()
            return response
        except Exception as e:
            print(f"[{get_timestamp()}] 💥 Error generating response: {str(e)}")
            raise

# Пример использования
if __name__ == "__main__":
    model_path = "C:/Users/home/.lmstudio/models/lmstudio-community/Qwen2.5-7B-Instruct-1M-GGUF/Qwen2.5-7B-Instruct-1M-Q4_K_M.gguf"
    prompt = "Название: Большой Сибирский Стендап | Новосибирск..."  # Замените на ваш промпт
    
    local_model = LocalModel()
    local_model.initialize_model(model_path)
    
    def generate():
        response = local_model.generate_response(prompt, model_path)
        print(f"[{get_timestamp()}] Ответ: {response}")

    thread = threading.Thread(target=generate)
    thread.start()

    while thread.is_alive():
        print(f"[{get_timestamp()}] Системная информация во время генерации:")
        print(check_system_info())
        time.sleep(1)

    thread.join()