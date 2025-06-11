from src.local_model import LocalModel
from src.config import MODEL_NAME
# Initialize the model
model_path = "C:/Users/home/.lmstudio/models/lmstudio-community/Qwen2.5-7B-Instruct-1M-GGUF/Qwen2.5-7B-Instruct-1M-Q4_K_M.gguf"
model = LocalModel(model_path)

# Example conversation
messages = [
    {"role": "user", "content": "Hello, how are you?"}
]

# Generate response
response = model.generate_structured_response(messages, MODEL_NAME)
print("Model response:", response["choices"][0]["message"]["content"])

