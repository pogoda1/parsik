from llama_cpp import Llama
import os
import ctypes
import platform
import psutil
import GPUtil
import time
from src.api import PromptManager
from src.config import MODEL_NAME, MODEL_NAME_VERY_SMART
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

def check_cuda_available():
    try:
        if platform.system() == "Windows":
            cuda = ctypes.CDLL("nvcuda.dll")
            return "CUDA доступен"
    except:
        return "CUDA недоступен"
    return "Неизвестно"

print("CUDA status:", check_cuda_available())
print("\nСистемная информация до запуска:")
print(check_system_info())
    # model_path="C:/Users/home/.lmstudio/models/lmstudio-community/Qwen2.5-7B-Instruct-1M-GGUF/Qwen2.5-7B-Instruct-1M-Q4_K_M.gguf",

print("\nИнициализация модели...")
model = Llama(
    
    model_path="C:/Users/home/.lmstudio/models/lmstudio-community/Qwen2.5-7B-Instruct-1M-GGUF/Qwen2.5-7B-Instruct-1M-Q4_K_M.gguf",
    n_ctx=8192,
    n_gpu_layers=35,
    n_threads=os.cpu_count(),
    n_batch=1024,
    verbose=False,
    grammar_path="json",
    echo=False
)

print("\nТестирование вывода модели...")
print("\nСистемная информация во время генерации:")
promptManager = PromptManager()

start_time = time.time()
output = model(promptManager.prepare_prompt("Название: Мотокросс. Первое занятие. Дата: с 2025-06-04T12:15:00.000Z до 2025-06-30T17:40:00.000Z. Цена: 5200. Адрес: Ленинграддер. Новожилово, Приозерское ш., 3к2, Санкт-Петербург. Категория: спорт"), 
    max_tokens=200,
    temperature=0.1,
    top_p=0.1,
    top_k=10,
    stream=False
)
end_time = time.time()
generation_time = end_time - start_time

print(check_system_info())
print(f"\nВремя генерации: {generation_time:.2f} секунд")
print("\nГенерация завершена.") 
print(output["choices"][0])