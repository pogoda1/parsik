from datetime import datetime
from typing import List, Dict, Any
from llama_cpp import Llama
import os

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class LocalModel:
    def __init__(self):
        self.model = None
        
    def initialize_model(self, model_path: str):
        print(f"[{get_timestamp()}] 🔧 Initializing local model from {model_path}")
        try:
            self.model = Llama(
                model_path=model_path,
                n_ctx=8192,
                n_gpu_layers=35,
                n_threads=os.cpu_count(),
                n_batch=1024,
                max_tokens=400,
                verbose=False,
                grammar_path="json",
                echo=False
            )
            print(f"[{get_timestamp()}] ✅ Model initialized successfully")
        except Exception as e:
            print(f"[{get_timestamp()}] 💥 Error initializing model: {str(e)}")
            raise

    def generate_response(self, prompt: str, model_path: str, temperature: float = 0.8) -> str:
        """
        Generate a response using the specified model
        """
        if not self.model or self.model.model_path != model_path:
            self.initialize_model(model_path)
            
        try:
            output = self.model(
                prompt,
                temperature=temperature,
            )
            print(f"[{get_timestamp()}] 📡 prompt: {prompt}")
            print(f"[{get_timestamp()}] 📡 output: {output}")
            # Extract the generated text
            response = output["choices"][0]["text"].strip()
            return response
        except Exception as e:
            print(f"[{get_timestamp()}] 💥 Error generating response: {str(e)}")
            raise 